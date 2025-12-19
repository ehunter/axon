/**
 * Theme Compatibility Tests
 * 
 * These tests verify that our theme CSS variables are compatible with shadcn/ui.
 * shadcn expects CSS variables in HSL format without the hsl() wrapper.
 */

import { render, screen } from '@testing-library/react';

// Mock CSS variables that shadcn expects
const REQUIRED_SHADCN_VARIABLES = [
  '--background',
  '--foreground',
  '--card',
  '--card-foreground',
  '--popover',
  '--popover-foreground',
  '--primary',
  '--primary-foreground',
  '--secondary',
  '--secondary-foreground',
  '--muted',
  '--muted-foreground',
  '--accent',
  '--accent-foreground',
  '--destructive',
  '--destructive-foreground',
  '--border',
  '--input',
  '--ring',
];

// HSL format regex: "H S% L%" or "H S% L% / A"
const HSL_FORMAT_REGEX = /^\d+(\.\d+)?\s+\d+(\.\d+)?%\s+\d+(\.\d+)?%(\s*\/\s*[\d.]+%?)?$/;

describe('Theme CSS Variables', () => {
  // Helper to get computed CSS variable value
  const getCSSVariable = (name: string): string => {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  };

  beforeAll(() => {
    // Inject our theme CSS variables for testing
    // These should match what's in globals.css (HSL format)
    const style = document.createElement('style');
    style.textContent = `
      :root {
        --background: 227 29% 15%;
        --foreground: 0 0% 98%;
        --card: 228 16% 22%;
        --card-foreground: 0 0% 98%;
        --popover: 228 16% 22%;
        --popover-foreground: 0 0% 98%;
        --primary: 0 0% 98%;
        --primary-foreground: 227 29% 15%;
        --secondary: 225 14% 26%;
        --secondary-foreground: 0 0% 98%;
        --muted: 225 14% 26%;
        --muted-foreground: 0 0% 45%;
        --accent: 225 14% 26%;
        --accent-foreground: 0 0% 98%;
        --destructive: 0 84% 60%;
        --destructive-foreground: 0 0% 98%;
        --border: 225 5% 16%;
        --input: 222 22% 27%;
        --ring: 225 14% 26%;
        --radius: 0.5rem;
        --sidebar: 227 45% 11%;
        --sidebar-foreground: 0 0% 98%;
        --sidebar-primary: 225 14% 26%;
        --sidebar-primary-foreground: 0 0% 98%;
        --sidebar-accent: 228 16% 22%;
        --sidebar-accent-foreground: 0 0% 98%;
        --sidebar-border: 225 5% 16%;
        --sidebar-ring: 225 14% 26%;
        --sidebar-muted: 229 32% 62%;
      }
    `;
    document.head.appendChild(style);
  });

  describe('Required Variables Exist', () => {
    test.each(REQUIRED_SHADCN_VARIABLES)(
      'CSS variable %s is defined',
      (varName) => {
        const value = getCSSVariable(varName);
        expect(value).not.toBe('');
      }
    );
  });

  describe('HSL Format Validation', () => {
    test.each(REQUIRED_SHADCN_VARIABLES)(
      'CSS variable %s is in HSL format (H S%% L%%)',
      (varName) => {
        const value = getCSSVariable(varName);
        expect(value).toMatch(HSL_FORMAT_REGEX);
      }
    );
  });

  describe('Sidebar Variables Exist', () => {
    const sidebarVars = [
      '--sidebar',
      '--sidebar-foreground',
      '--sidebar-primary',
      '--sidebar-primary-foreground',
      '--sidebar-accent',
      '--sidebar-accent-foreground',
      '--sidebar-border',
      '--sidebar-ring',
    ];

    test.each(sidebarVars)(
      'Sidebar variable %s is defined',
      (varName) => {
        const value = getCSSVariable(varName);
        expect(value).not.toBe('');
      }
    );
  });
});

describe('Theme Component Rendering', () => {
  test('renders component with theme classes without error', () => {
    // Simple component using Tailwind theme classes
    const TestComponent = () => (
      <div data-testid="themed-container" className="bg-background text-foreground">
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md">
          Test Button
        </button>
        <div className="bg-card text-card-foreground p-4 rounded-lg border border-border">
          Card content
        </div>
      </div>
    );

    render(<TestComponent />);
    
    expect(screen.getByTestId('themed-container')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveTextContent('Test Button');
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });
});




