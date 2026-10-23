import {ReactNode} from 'react';
export const format=(v:string|null)=>v?new Date(v).toLocaleString():'Not set';
export function ErrorBox({error}:{error:unknown}){return error?<div role="alert" className="error">{error instanceof Error?error.message:String(error)}</div>:null}
export function Badge({text}:{text:string}){return <span className={`badge ${text.toLowerCase()}`}>{text.replaceAll('_',' ')}</span>}
export function Panel({title,children}:{title?:string;children:ReactNode}){return <section className="panel">{title&&<h2>{title}</h2>}{children}</section>}
export function Loading(){return <p role="status">Loading records…</p>}
