import {Navigate,Outlet} from 'react-router-dom';import {useAuth} from '../features/auth/AuthContext';import {Role} from '../types';
export function Guard({role}:{role:Role}){const {user}=useAuth();return !user?<Navigate to="/login" replace/>:user.role!==role?<Navigate to={`/${user.role.toLowerCase()}/dashboard`} replace/>:<Outlet/>}
