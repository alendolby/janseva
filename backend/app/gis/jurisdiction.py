import json
from sqlalchemy import select, func
from shapely.geometry import shape, Point, MultiPolygon
from geoalchemy2.shape import from_shape
from app.models.entities import Ward, LocalBody, District
from fastapi import HTTPException

def point(db,lat,lon):
    return from_shape(Point(lon,lat),srid=4326) if db.bind.dialect.name=="postgresql" else f"POINT({lon} {lat})"
def boundary_value(db,geojson):
    try:
        geom=shape(geojson)
        if geom.geom_type not in ("Polygon","MultiPolygon") or not geom.is_valid or geom.is_empty:
            raise ValueError()
        if not (-180<=geom.bounds[0]<=geom.bounds[2]<=180 and -90<=geom.bounds[1]<=geom.bounds[3]<=90):
            raise ValueError()
        if geom.geom_type=="Polygon": geom=MultiPolygon([geom])
        return from_shape(geom,srid=4326) if db.bind.dialect.name=="postgresql" else json.dumps(geojson)
    except (ValueError,TypeError,KeyError): raise HTTPException(422,"Boundary must be valid WGS84 Polygon or MultiPolygon")
def jurisdiction(db,lat,lon):
    if db.bind.dialect.name=="postgresql":
        wards=db.scalars(select(Ward).where(func.ST_Covers(Ward.geometry,func.ST_SetSRID(func.ST_MakePoint(lon,lat),4326)))).all()
    else:
        wards=[w for w in db.scalars(select(Ward)) if shape(json.loads(w.boundary)).covers(Point(lon,lat))]
    eligible=[w for w in wards if w.verified or __import__('app.core.config',fromlist=['settings']).settings().demo_mode]
    if len(eligible)!=1: return None
    ward=eligible[0]; body=db.get(LocalBody,ward.local_body_id);district=db.get(District,body.district_id)
    return {"ward_id":ward.id,"ward":ward.name,"local_body_id":body.id,"local_body":body.name,
        "district_id":district.id,"district":district.name,"source":ward.source,"verified":ward.verified}
