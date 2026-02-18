
import { AuthProvider } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import WidgetContainer from './AppWidget';

function App() {
  return (
    <AuthProvider>
      <div className="relative">
        <LandingPage />
        <WidgetContainer />
      </div>
    </AuthProvider>
  );
}

export default App;

