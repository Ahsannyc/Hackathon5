import React from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'CloudFlow Support',
  description: 'CloudFlow Customer Success Support Portal',
};

export default function SupportFormLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
