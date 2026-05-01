import React from 'react';
import SupportForm from './SupportForm';

export const metadata = {
  title: 'Support Form | CloudFlow',
  description: 'Submit your support request to our team',
};

export default function SupportPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 py-12 px-4">
      <SupportForm />
    </main>
  );
}
