from datetime import timedelta
from math import radians, sin, cos, atan2, sqrt
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography
from sklearn.metrics.pairwise import cosine_similarity
from app.ml.baseline import load_model
from app.models.entities import Case, CaseLocation, now

def distance(a,b,c,d):
    p,q=radians(c-a),radians(d-b)
    h=sin(p/2)**2+cos(radians(a))*cos(radians(c))*sin(q/2)**2
    return 6371000*2*atan2(sqrt(h),sqrt(max(0,1-h)))
def similarity(a,b,metres):
    vect=load_model().named_steps["tfidf"]
    cosine=float(cosine_similarity(vect.transform([a]),vect.transform([b]))[0,0])
    return 0.8*cosine+0.2*max(0,1-metres/150)
def related(db,text,category_id,latitude,longitude):
    query=select(Case,CaseLocation).join(CaseLocation,CaseLocation.case_id==Case.id).where(
       Case.category_id==category_id,Case.created_at>=now()-timedelta(days=30))
    if db.bind.dialect.name=="postgresql":
        query=query.where(func.ST_DWithin(cast(CaseLocation.geometry,Geography),
            cast(func.ST_SetSRID(func.ST_MakePoint(longitude,latitude),4326),Geography),150))
    rows=db.execute(query.order_by(Case.created_at.desc()).limit(500)).all()
    matches=[]
    for case,loc in rows:
        metres=distance(latitude,longitude,loc.latitude,loc.longitude)
        if metres<=150:
            score=similarity(text,case.title+" "+case.description,metres)
            if score>=0.45: matches.append({"case":case,"score":score,"distance_m":round(metres)})
    return matches
