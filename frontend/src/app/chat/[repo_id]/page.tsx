// frontend/src/app/chat/[repo_id]/page.tsx

"use client"; // クライアントコンポーネント

import { useState } from 'react';
import { useParams } from 'next/navigation'; // URLパラメータを取得
import apiClient from '@/lib/api';
import { isAxiosError } from 'axios'; // ★ 1. これを追加

// メッセージの型定義
type Message = {
  sender: 'user' | 'ai';
  text: string;
};

export default function ChatPage() {
  const params = useParams();
  const repo_id = params.repo_id as string; // URLから repo_id を取得

  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: Message = { sender: 'user', text: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);
    setError(null);

    try {
      // 1. FastAPIの /chat エンドポイントを叩く
      const response = await apiClient.post('/chat', {
        repo_id: repo_id,
        query: query,
      });

      const aiMessage: Message = { sender: 'ai', text: response.data.answer };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (err: unknown) { // ★ 2. any を unknown に変更
      console.error(err);
      // ★ 3. エラーハンドリングを修正
      let message = 'Failed to get answer.';
      if (isAxiosError(err) && err.response?.data?.detail) {
        message = err.response.data.detail;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm p-4 text-center">
        <h1 className="text-xl font-semibold text-gray-800">
          Chat with: <span className="font-mono text-indigo-600">{repo_id}</span>
        </h1>
      </header>

      {/* チャット履歴 */}
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-lg p-3 rounded-lg shadow-md ${
                msg.sender === 'user' 
                  ? 'bg-indigo-500 text-white' 
                  : 'bg-white text-gray-800'
              }`}
            >
              {/* 改行を反映させるために pre-wrap を使う */}
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 p-3 rounded-lg shadow-md">
              <p>Thinking...</p>
            </div>
          </div>
        )}
         {error && (
            <p className="text-sm text-center text-red-600">
              Error: {error}
            </p>
          )}
      </main>

      {/* 入力フォーム */}
      <footer className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleChatSubmit} className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about the repository..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="py-2 px-4 rounded-md text-white font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}