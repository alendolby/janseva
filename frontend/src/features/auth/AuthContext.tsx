import {createContext,useContext,useState,ReactNode} from 'react';
import {User} from '../../types';import {api,setToken} from '../../api/client';
const Context=createContext<{user:User|null;signIn:(u:User,t:string)=>void;signOut:()=>Promise<void>;setUser:(u:User)=>void}>(null!);
export function AuthProvider({children}:{children:ReactNode}){
 const [user,setUser]=useState<User|null>(null);
 return <Context.Provider value={{user,setUser,signIn:(u,t)=>{setToken(t);setUser(u)},signOut:async()=>{await api('/auth/logout',{method:'POST'});setToken('');setUser(null)}}}>{children}</Context.Provider>
}
export const useAuth=()=>useContext(Context);
