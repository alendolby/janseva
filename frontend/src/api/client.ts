let accessToken='';
export function setToken(token:string){accessToken=token}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{
 const headers=new Headers(options.headers);if(accessToken)headers.set('Authorization',`Bearer ${accessToken}`);
 if(options.body && !(options.body instanceof FormData))headers.set('Content-Type','application/json');
 const res=await fetch('/api'+path,{...options,headers});
 if(!res.ok){const data=await res.json().catch(()=>({}));throw new Error(data.error?.message || 'Unable to complete the request')}
 return res.json();
}
export const post=<T=any>(path:string,body:unknown)=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
export async function download(path:string){
 const res=await fetch('/api'+path,{headers:{Authorization:`Bearer ${accessToken}`}});
 if(!res.ok)throw new Error('Evidence could not be downloaded');
 return URL.createObjectURL(await res.blob());
}
