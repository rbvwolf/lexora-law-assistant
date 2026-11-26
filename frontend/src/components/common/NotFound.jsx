import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';

const NotFound = ({ homePath = '/' }) => (
  <div className="flex-1 flex flex-col items-center justify-center text-center p-10 gap-3">
    <div className="w-12 h-12 rounded-full bg-teal/10 text-teal flex items-center justify-center"><Compass size={22} /></div>
    <h2 className="text-lg font-bold text-navy">Sayfa bulunamadı</h2>
    <p className="text-sm text-slate-500">Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir.</p>
    <Link to={homePath} className="mt-2 bg-navy text-white text-sm font-bold px-5 py-2.5 rounded-xl hover:bg-navy/90">Geri dön</Link>
  </div>
);

export default NotFound;
