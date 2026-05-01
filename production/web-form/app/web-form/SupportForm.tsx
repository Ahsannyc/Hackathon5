'use client';

import React, { useState } from 'react';
import { Mail, AlertCircle, CheckCircle, Loader2, Send, RefreshCw } from 'lucide-react';

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

interface SubmissionResponse {
  success: boolean;
  ticket_id?: string;
  message?: string;
  error?: string;
}

interface FormErrors {
  [key: string]: string;
}

export default function SupportForm() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    category: 'general',
    priority: 'medium',
    message: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [messageCharCount, setMessageCharCount] = useState(0);

  // Validation patterns
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const nameRegex = /^[a-zA-Z\s'-]{2,}$/;

  // Validate individual field
  const validateField = (name: string, value: string): string => {
    switch (name) {
      case 'name':
        if (!value.trim()) return 'Name is required';
        if (value.trim().length < 2) return 'Name must be at least 2 characters';
        if (!nameRegex.test(value)) return 'Name can only contain letters, spaces, hyphens, and apostrophes';
        return '';

      case 'email':
        if (!value.trim()) return 'Email is required';
        if (!emailRegex.test(value)) return 'Please enter a valid email address';
        return '';

      case 'subject':
        if (!value.trim()) return 'Subject is required';
        if (value.trim().length < 5) return 'Subject must be at least 5 characters';
        if (value.trim().length > 100) return 'Subject must not exceed 100 characters';
        return '';

      case 'message':
        if (!value.trim()) return 'Message is required';
        if (value.trim().length < 10) return 'Message must be at least 10 characters';
        if (value.trim().length > 5000) return 'Message must not exceed 5000 characters';
        return '';

      case 'category':
        if (!value) return 'Please select a category';
        return '';

      case 'priority':
        if (!value) return 'Please select a priority';
        return '';

      default:
        return '';
    }
  };

  // Handle input change
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Update character count for message
    if (name === 'message') {
      setMessageCharCount(value.length);
    }

    // Clear error for this field if it exists
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  // Validate all fields
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    Object.keys(formData).forEach(key => {
      const error = validateField(key, formData[key as keyof FormData]);
      if (error) {
        newErrors[key] = error;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitError(null);

    // Validate form
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const formDataToSubmit = new FormData();
      formDataToSubmit.append('customer_name', formData.name);
      formDataToSubmit.append('customer_email', formData.email);
      formDataToSubmit.append('subject', formData.subject);
      formDataToSubmit.append('priority', formData.priority);
      formDataToSubmit.append('message', formData.message);

      const response = await fetch('http://localhost:8000/api/form/submit', {
        method: 'POST',
        body: formDataToSubmit,
      });

      const data: SubmissionResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to submit form');
      }

      // Success
      setSubmitted(true);
      setTicketId(data.ticket_id || (data as any).submission_id || null);
      setAiResponse((data as any).ai_response || null);
      setFormData({
        name: '',
        email: '',
        subject: '',
        category: 'general',
        priority: 'medium',
        message: '',
      });
      setMessageCharCount(0);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred. Please try again.';
      setSubmitError(errorMessage);
      console.error('Form submission error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Reset form to initial state
  const handleResetForm = () => {
    setSubmitted(false);
    setTicketId(null);
    setAiResponse(null);
    setSubmitError(null);
    setFormData({
      name: '',
      email: '',
      subject: '',
      category: 'general',
      priority: 'medium',
      message: '',
    });
    setMessageCharCount(0);
    setErrors({});
  };

  // Success state
  if (submitted) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-green-900 mb-2">Thank You!</h2>
          <p className="text-green-700 mb-6">Your support request has been submitted successfully.</p>

          {ticketId && (
            <div className="bg-white rounded-lg p-6 mb-6 border-2 border-green-200">
              <p className="text-gray-600 text-sm mb-2">Your Ticket ID</p>
              <p className="text-3xl font-bold text-green-600 font-mono">{ticketId}</p>
              <p className="text-gray-500 text-xs mt-2">Please keep this ID for your records</p>
            </div>
          )}

          {aiResponse && (
            <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 mb-6">
              <p className="text-purple-900 font-semibold text-sm mb-3">AI Assistant Response:</p>
              <p className="text-purple-800 text-sm leading-relaxed">{aiResponse}</p>
              <p className="text-purple-600 text-xs mt-3">This is an AI-generated response. For urgent matters, our team will follow up shortly.</p>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-blue-700 text-sm">
              {aiResponse
                ? "Our support team will review your request and follow up with additional assistance if needed. You'll receive updates via email."
                : "Our support team will review your request and get back to you within 24 hours. You'll receive updates via email."
              }
            </p>
          </div>

          <button
            onClick={handleResetForm}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold py-3 px-8 rounded-lg transition-all duration-200 hover:shadow-lg"
          >
            <RefreshCw className="w-5 h-5" />
            Submit Another Request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-white px-8 py-6 border-b-2 border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded bg-purple-600 flex items-center justify-center">
              <span className="text-white font-bold">📝</span>
            </div>
            <h1 className="text-2xl font-bold text-purple-600">Create AI Ticket</h1>
          </div>
          <p className="text-gray-600 text-sm">Fill out the form. Our AI will route it to Kafka instantly.</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {/* Error Alert */}
          {submitError && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-800">Submission Failed</p>
                <p className="text-red-700 text-sm">{submitError}</p>
              </div>
            </div>
          )}

          {/* Row 1: Name and Email */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
                Full Name <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
                className={`w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all ${
                  errors.name ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
              />
              {errors.name && (
                <p className="text-red-600 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.name}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address <span className="text-red-600">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="john@example.com"
                  className={`w-full pl-10 pr-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all ${
                    errors.email ? 'border-red-500 bg-red-50' : 'border-gray-300'
                  }`}
                />
              </div>
              {errors.email && (
                <p className="text-red-600 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.email}
                </p>
              )}
            </div>
          </div>

          {/* Row 2: Subject */}
          <div>
            <label htmlFor="subject" className="block text-sm font-semibold text-gray-700 mb-2">
              Subject <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Briefly describe your issue"
              maxLength={100}
              className={`w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all ${
                errors.subject ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
            />
            <div className="flex justify-between items-start mt-1">
              {errors.subject && (
                <p className="text-red-600 text-sm flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.subject}
                </p>
              )}
              <p className="text-gray-500 text-xs ml-auto">{formData.subject.length}/100</p>
            </div>
          </div>

          {/* Row 3: Category and Priority */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Category */}
            <div>
              <label htmlFor="category" className="block text-sm font-semibold text-gray-700 mb-2">
                Category <span className="text-red-600">*</span>
              </label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                className={`w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all appearance-none bg-white cursor-pointer ${
                  errors.category ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 1rem center',
                  paddingRight: '2.5rem',
                }}
              >
                <option value="general">General Inquiry</option>
                <option value="technical">Technical Support</option>
                <option value="billing">Billing & Pricing</option>
                <option value="feedback">Feature Feedback</option>
                <option value="bug_report">Bug Report</option>
              </select>
              {errors.category && (
                <p className="text-red-600 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.category}
                </p>
              )}
            </div>

            {/* Priority */}
            <div>
              <label htmlFor="priority" className="block text-sm font-semibold text-gray-700 mb-2">
                Priority <span className="text-red-600">*</span>
              </label>
              <select
                id="priority"
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className={`w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all appearance-none bg-white cursor-pointer ${
                  errors.priority ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 1rem center',
                  paddingRight: '2.5rem',
                }}
              >
                <option value="low">Low - General question</option>
                <option value="medium">Medium - Normal issue</option>
                <option value="high">High - Urgent issue</option>
              </select>
              {errors.priority && (
                <p className="text-red-600 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.priority}
                </p>
              )}
            </div>
          </div>

          {/* Message */}
          <div>
            <label htmlFor="message" className="block text-sm font-semibold text-gray-700 mb-2">
              Message <span className="text-red-600">*</span>
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              placeholder="Please provide detailed information about your request..."
              maxLength={5000}
              rows={6}
              className={`w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none ${
                errors.message ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
            />
            <div className="flex justify-between items-start mt-1">
              {errors.message && (
                <p className="text-red-600 text-sm flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.message}
                </p>
              )}
              <p className="text-gray-500 text-xs ml-auto">{messageCharCount}/5000</p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4 flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 rounded-lg transition-all duration-200 hover:shadow-lg disabled:shadow-none"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Submit Request
                </>
              )}
            </button>
          </div>

          {/* Helper text */}
          <p className="text-gray-500 text-xs text-center">
            <span className="text-red-600">*</span> indicates required fields. We'll get back to you within 24 hours.
          </p>
        </form>
      </div>
    </div>
  );
}
