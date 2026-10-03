'use client';

import React from 'react';
import Link from 'next/link';

export interface FooterLink {
  label: string;
  href: string;
}

export interface FooterSection {
  title: string;
  links: FooterLink[];
}

export interface FooterProps {
  sections?: FooterSection[];
  copyright?: string;
  companyName?: string;
  socialLinks?: { label: string; href: string; icon?: React.ReactNode }[];
  className?: string;
}

const defaultSections: FooterSection[] = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '/features' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Security', href: '/security' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '/about' },
      { label: 'Blog', href: '/blog' },
      { label: 'Careers', href: '/careers' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '/docs' },
      { label: 'Help Center', href: '/help' },
      { label: 'Community', href: '/community' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy', href: '/privacy' },
      { label: 'Terms', href: '/terms' },
    ],
  },
];

const Footer: React.FC<FooterProps> = ({
  sections = defaultSections,
  copyright,
  companyName = 'Gated Communities',
  socialLinks = [],
  className = '',
}) => {
  const currentYear = new Date().getFullYear();
  const copyrightText = copyright || `© ${currentYear} ${companyName}. All rights reserved.`;

  return (
    <footer className={`bg-gray-50 border-t border-gray-200 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1 mb-8 lg:mb-0">
            <Link href="/" className="text-lg font-semibold text-gray-900">
              {companyName}
            </Link>
            <p className="mt-2 text-sm text-gray-500">
              Secure, gated communities for exclusive content and collaboration.
            </p>
            {socialLinks.length > 0 && (
              <div className="flex gap-4 mt-4">
                {socialLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={link.label}
                  >
                    {link.icon || link.label}
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Link sections */}
          {sections.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">
                {section.title}
              </h3>
              <ul className="mt-4 space-y-2">
                {section.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-400 text-center">{copyrightText}</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
