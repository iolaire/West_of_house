/**
 * PageHeader Component
 * Feature: grimoire-frontend
 *
 * Displays the app logo, title, and navigation
 * Includes About link that triggers a full-screen modal
 */

import React, { useState } from 'react';
import AboutModal from './AboutModal';
import '../styles/PageHeader.css';

/**
 * PageHeader component
 *
 * Shows the West of Haunted House branding and navigation
 */
const PageHeader: React.FC = () => {
  const [isAboutModalOpen, setIsAboutModalOpen] = useState<boolean>(false);

  const openAboutModal = () => {
    setIsAboutModalOpen(true);
    document.body.style.overflow = 'hidden';
  };

  const closeAboutModal = () => {
    setIsAboutModalOpen(false);
    document.body.style.overflow = '';
  };

  return (
    <>
      <header className="page-header" role="banner">
        <div className="header-content">
          <div className="header-logo-section">
            <img
              src="/images/assets/WestofHauntedHouse_logo.jpg"
              alt="West of Haunted House Logo"
              className="header-logo"
            />
            <h1 className="header-title">West of Haunted House</h1>
          </div>

          <nav className="header-nav" role="navigation" aria-label="Main navigation">
            <button
              className="header-link about-link"
              onClick={openAboutModal}
              aria-label="Open About dialog"
            >
              About
            </button>
          </nav>
        </div>
      </header>

      {isAboutModalOpen && (
        <AboutModal onClose={closeAboutModal} />
      )}
    </>
  );
};

export default PageHeader;