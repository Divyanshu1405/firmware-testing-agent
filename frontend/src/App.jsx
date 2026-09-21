import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import DashboardPage from "./pages/DashboardPage";
import FirmwarePage from "./pages/FirmwarePage";
import SpecEditorPage from "./pages/SpecEditorPage";
import RequirementsPage from "./pages/RequirementsPage";
import PipelinePage from "./pages/PipelinePage";
import TracesPage from "./pages/TracesPage";
import VerdictsPage from "./pages/VerdictsPage";
import ReportPage from "./pages/ReportPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/firmware" element={<FirmwarePage />} />
        <Route path="/spec" element={<SpecEditorPage />} />
        <Route path="/requirements" element={<RequirementsPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/traces" element={<TracesPage />} />
        <Route path="/verdicts" element={<VerdictsPage />} />
        <Route path="/report" element={<ReportPage />} />
      </Route>
    </Routes>
  );
}