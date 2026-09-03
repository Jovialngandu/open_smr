import { createBrowserRouter } from 'react-router-dom';
import LayoutPublic from './components/common/layout/LayoutPublic';
import Home from './pages/public/Home';
import Login from './pages/auth/Login';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: <LayoutPublic />,
    children: [
      {
        path: '/',
        element: <Home />,
      },
    ],
  },
]);