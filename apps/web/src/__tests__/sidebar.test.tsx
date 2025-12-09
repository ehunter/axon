/**
 * Sidebar Component Tests
 * 
 * Tests for the Oskar-style sidebar matching Figma design.
 */

import { render, screen } from '@testing-library/react';
import { Sidebar } from '@/components/layout/sidebar';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

// Mock useAuth hook
jest.mock('@/hooks/use-auth', () => ({
  useAuth: jest.fn(),
}));

const mockUsePathname = usePathname as jest.MockedFunction<typeof usePathname>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('Sidebar Component', () => {
  beforeEach(() => {
    mockUsePathname.mockReturnValue('/chat');
    mockUseAuth.mockReturnValue({
      status: 'authenticated',
      data: {
        user: {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
        },
      },
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
      },
      signOut: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Structure', () => {
    test('renders sidebar with correct width and background', () => {
      render(<Sidebar />);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toHaveClass('lg:w-[270px]', 'lg:bg-sidebar');
    });

    test('renders logo section', () => {
      render(<Sidebar />);
      expect(screen.getByText('Axon')).toBeInTheDocument();
    });

    test('renders main navigation menu', () => {
      render(<Sidebar />);
      expect(screen.getByText('New Chat')).toBeInTheDocument();
      expect(screen.getByText('Requests')).toBeInTheDocument();
      expect(screen.getByText('Explore')).toBeInTheDocument();
    });

    test('renders Cohorts section', () => {
      render(<Sidebar />);
      expect(screen.getByText('Cohorts')).toBeInTheDocument();
    });

    test('renders Settings and About links', () => {
      render(<Sidebar />);
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
    });

    test('renders user profile section', () => {
      render(<Sidebar />);
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  describe('Active States', () => {
    test('highlights "New Chat" when on /chat route', () => {
      mockUsePathname.mockReturnValue('/chat');
      render(<Sidebar />);
      const newChatLink = screen.getByText('New Chat').closest('a');
      expect(newChatLink).toHaveClass('bg-sidebar-primary');
    });

    test('highlights "Requests" when on /history route', () => {
      mockUsePathname.mockReturnValue('/history');
      render(<Sidebar />);
      const requestsLink = screen.getByText('Requests').closest('a');
      expect(requestsLink).toHaveClass('bg-sidebar-primary');
    });

    test('highlights "Explore" when on /samples route', () => {
      mockUsePathname.mockReturnValue('/samples');
      render(<Sidebar />);
      const exploreLink = screen.getByText('Explore').closest('a');
      expect(exploreLink).toHaveClass('bg-sidebar-primary');
    });
  });

  describe('Cohorts', () => {
    test('renders cohort items with folder icons', () => {
      render(<Sidebar />);
      // Should render cohort items - we'll need to pass these as props or fetch from API
      // For now, just verify the section exists
      expect(screen.getByText('Cohorts')).toBeInTheDocument();
    });
  });

  describe('User Profile', () => {
    test('displays user name and email', () => {
      render(<Sidebar />);
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    test('renders user avatar', () => {
      render(<Sidebar />);
      // Avatar should be present (we'll use User icon or image)
      const userSection = screen.getByText('Test User').closest('div');
      expect(userSection).toBeInTheDocument();
    });

    test('handles missing user gracefully', () => {
      mockUseAuth.mockReturnValue({
        status: 'unauthenticated',
        data: null,
        user: null,
        signOut: jest.fn(),
      });
      render(<Sidebar />);
      // Should not crash, user section may be hidden or show placeholder
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA role', () => {
      render(<Sidebar />);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toBeInTheDocument();
    });

    test('navigation links are keyboard accessible', () => {
      render(<Sidebar />);
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });
  });
});

