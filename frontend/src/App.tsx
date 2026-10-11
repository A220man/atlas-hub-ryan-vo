import React, { useState } from "react";
import { Navbar } from "./components/Navbar.tsx";
import { PresentationList } from "./components/PresentationList.tsx";
import { PresentationDetail } from "./components/PresentationDetail.tsx";
import { CreateModal } from "./components/CreateModal.tsx";

export const App: React.FC = () => {
  const [selectedPresentationId, setSelectedPresentationId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);

  return (
    <div className="app-layout">
      <Navbar
        onOpenCreate={() => setIsCreateOpen(true)}
        onNavigateHome={() => setSelectedPresentationId(null)}
      />

      <main className="main-content">
        {selectedPresentationId ? (
          <PresentationDetail
            presentationId={selectedPresentationId}
            onBack={() => setSelectedPresentationId(null)}
          />
        ) : (
          <PresentationList
            onSelectPresentation={(id) => setSelectedPresentationId(id)}
            onOpenCreate={() => setIsCreateOpen(true)}
          />
        )}
      </main>

      <CreateModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={(newId) => {
          setIsCreateOpen(false);
          setSelectedPresentationId(newId);
        }}
      />

      <footer className="app-footer">
        <div>atlas-hub-ryan-vo &bull; Ryan Vo &lt;ryandtvo@gmail.com&gt;</div>
        <div className="footer-links">
          <span>OIDC & Keycloak SAML Brokered</span>
          <span>Native OpenXML PPTX Generation</span>
          <span>Fail-Closed Attribution Guard</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
