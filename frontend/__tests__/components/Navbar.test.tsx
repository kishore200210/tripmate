import { render, screen } from '@testing-library/react';
import { Navbar } from '@/components/layout/Navbar';

// Mock Next.js navigation and router hooks
jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}));

describe('Navbar Component', () => {
  it('renders the branding correctly', () => {
    render(<Navbar />);
    expect(screen.getByText('TripMate')).toBeInTheDocument();
  });

  it('renders all navigation links', () => {
    render(<Navbar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Destinations')).toBeInTheDocument();
    expect(screen.getByText('My Trips')).toBeInTheDocument();
    expect(screen.getByText('Concierge')).toBeInTheDocument();
  });

  it('highlights the active link based on pathname', () => {
    render(<Navbar />);
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveClass('text-blue-600'); // active state
  });
});
