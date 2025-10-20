// frontend/src/app/page.tsx

"use client"; // このページがクライアントコンポーネントであることを示す

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // App Router 用のルーター
import apiClient from '@/lib/api';
import { isAxiosError } from 'axios'; // ★ 1. これを追加

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter(); // ページ遷移用

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // 1. FastAPIの /ingest エンドポイントを叩く
      const response = await apiClient.post('/ingest', { repo_url: repoUrl });
      
      const { repo_id, message } = response.data;
      console.log('Ingestion success:', message);

      // 2. 成功したらチャットページにリダイレクト
      router.push(`/chat/${repo_id}`);

    } catch (err: unknown) { // ★ 2. any を unknown に変更
      console.error(err);
      // ★ 3. エラーハンドリングを修正
      let message = 'An unexpected error occurred.';
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
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">
      <div className="w-full max-w-lg p-8 bg-white shadow-md rounded-lg">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-800">
          GitHub Repository Q&A
        </h1>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-700 mb-2">
              GitHub Repository URL
            </label>
            <input
              id="repoUrl"
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-2 px-4 rounded-md text-white font-semibold ${
              isLoading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700'
            } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
          >
            {isLoading ? 'Indexing... (This may take a minute)' : 'Start Chat'}
          </button>

          {error && (
            <p className="mt-4 text-sm text-center text-red-600">
              Error: {error}
            </p>
          )}
        </form>
      </div>
    </main>
  );
}