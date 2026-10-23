import {useEffect,useRef} from 'react';import * as maplibregl from 'maplibre-gl';import 'maplibre-gl/dist/maplibre-gl.css';import {api} from '../api/client';import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';maplibregl.setWorkerUrl(workerUrl);
export interface MapPoint{latitude:number;longitude:number;title?:string;case_id?:string;priority?:string}
function CivicMapImpl({points=[],onPick}:{points?:MapPoint[];onPick?:(lat:number,lon:number)=>void}){
 const el=useRef<HTMLDivElement>(null);const pick=useRef(onPick);pick.current=onPick;
 useEffect(()=>{if(!el.current)return;
  const map=new maplibregl.Map({container:el.current,center:[points[0]?.longitude??76.30,points[0]?.latitude??9.965],zoom:13,
   style:{version:8,sources:{osm:{type:'raster',tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],tileSize:256,attribution:'© OpenStreetMap contributors'}},layers:[{id:'osm',type:'raster',source:'osm'}]}});
  map.addControl(new maplibregl.NavigationControl());
  map.on('load',async()=>{
    if(points.length>1){
      map.addSource('cases',{type:'geojson',data:{type:'FeatureCollection',features:points.map(p=>({type:'Feature',properties:{},geometry:{type:'Point',coordinates:[p.longitude,p.latitude]}}))}});
      map.addLayer({id:'density',type:'heatmap',source:'cases',paint:{'heatmap-opacity':0.35,'heatmap-radius':30}});
    }
    try{const data=await api('/catalog');if(!map.getStyle())return;
      map.addSource('wards',{type:'geojson',data:{type:'FeatureCollection',features:data.wards.map((w:any)=>({type:'Feature',properties:{name:w.name},geometry:JSON.parse(w.boundary)}))}});
      map.addLayer({id:'ward-outline',type:'line',source:'wards',paint:{'line-color':'#437d60','line-width':2,'line-dasharray':[3,2]}});
    }catch{/* Complaint markers and coordinate entry remain available offline. */}
  });
  for(const p of points){const node=document.createElement('span');node.textContent=p.title||p.case_id||'Selected location';new maplibregl.Marker({color:p.priority==='Critical'?'#b33a29':'#206d5c'}).setLngLat([p.longitude,p.latitude]).setPopup(new maplibregl.Popup().setDOMContent(node)).addTo(map)}
  map.on('click',e=>pick.current?.(e.lngLat.lat,e.lngLat.lng));return()=>map.remove();
 },[JSON.stringify(points)]);
 return <div><div ref={el} className="map" aria-label="Complaint location map"/>{onPick&&<p className="muted">Click the map or enter coordinates below. Demo location: 9.965, 76.30.</p>}</div>
}

export default CivicMapImpl;
