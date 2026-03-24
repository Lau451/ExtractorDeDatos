import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ProgressView } from './ProgressView';

describe('ProgressView', () => {
  it('renders spinner and status text for classifying status', () => {
    render(<ProgressView status="classifying" errorCode={null} errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByText('Classifying document...')).toBeInTheDocument();
    // Loader2 icon should have animate-spin
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders extracting status text', () => {
    render(<ProgressView status="extracting" errorCode={null} errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByText('Extracting fields...')).toBeInTheDocument();
  });

  it('renders fallback for unknown status', () => {
    render(<ProgressView status="unknown_thing" errorCode={null} errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('renders error banner with GEMINI_ERROR message', () => {
    render(<ProgressView status="error" errorCode="GEMINI_ERROR" errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByText('Gemini failed to process this document. Try uploading again.')).toBeInTheDocument();
    expect(screen.getByText('Processing failed')).toBeInTheDocument();
  });

  it('error banner contains Try again button', () => {
    render(<ProgressView status="error" errorCode="GEMINI_ERROR" errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('renders fallback error message when errorCode is null', () => {
    render(<ProgressView status="error" errorCode={null} errorMessage={null} onRetry={() => {}} />);
    expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
  });
});
