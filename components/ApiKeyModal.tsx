import React, { useState } from 'react';

interface Props {
  onSubmit: (key: string) => void;
}

export const ApiKeyModal: React.FC<Props> = ({ onSubmit }) => {
  const [key, setKey] = useState('');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white p-8 rounded-2xl shadow-float max-w-md w-full mx-4">
        <h2 className="text-2xl font-semibold tracking-tight text-gray-900 mb-4">Enter Access Key</h2>
        <p className="text-gray-500 mb-6 leading-relaxed">
          To generate the real-time narrative analysis using the Gemini API, please provide your API Key.
        </p>
        <input
          type="password"
          className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all mb-4 text-lg"
          placeholder="Gemini API Key"
          value={key}
          onChange={(e) => setKey(e.target.value)}
        />
        <button
          onClick={() => onSubmit(key)}
          disabled={!key}
          className="w-full bg-black text-white py-4 rounded-xl font-medium text-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
        >
          Authenticate & Generate
        </button>
        <p className="text-xs text-center text-gray-400 mt-4">
          Keys are not stored. Used only for this session.
        </p>
      </div>
    </div>
  );
};