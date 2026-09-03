import { Outlet } from 'react-router-dom';

export default function LayoutPublic() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header / Navbar public */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}