'use client';

import { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Send, Search, Circle, Loader2, AlertCircle, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { socialService, Conversation as APIConversation, DirectMessage } from '@/lib/api/social';
import { useAuthStore } from '@/lib/auth/auth-store';

interface Conversation {
  id: string;
  participantName: string;
  participantAvatar?: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  isOnline: boolean;
  otherUserId: string;
}

interface Message {
  id: string;
  senderId: string;
  text: string;
  timestamp: string;
  isMine: boolean;
}

export default function MessagesPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [errorConversations, setErrorConversations] = useState<string | null>(null);
  const [errorMessages, setErrorMessages] = useState<string | null>(null);
  const [sendingMessage, setSendingMessage] = useState(false);

  const formatTimeAgo = (isoDate: string | null): string => {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const formatTimestamp = (isoDate: string | null): string => {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const fetchConversations = useCallback(async () => {
    if (!isAuthenticated()) {
      setLoadingConversations(false);
      return;
    }
    setLoadingConversations(true);
    setErrorConversations(null);
    try {
      const response = await socialService.getConversations();
      const mapped = response.conversations.map((c: APIConversation) => ({
        id: c.conversation_id,
        participantName: c.other_user_id,
        lastMessage: c.last_message,
        lastMessageTime: formatTimeAgo(c.last_message_at),
        unreadCount: 0,
        isOnline: false,
        otherUserId: c.other_user_id,
      }));
      setConversations(mapped);
      if (mapped.length > 0 && !selectedConversation) {
        setSelectedConversation(mapped[0].id);
      }
    } catch (err) {
      setErrorConversations(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setLoadingConversations(false);
    }
  }, [isAuthenticated, selectedConversation]);

  const fetchMessages = useCallback(async (conversationId: string) => {
    setLoadingMessages(true);
    setErrorMessages(null);
    try {
      const response = await socialService.getMessages(conversationId);
      const mapped = response.messages.map((m: DirectMessage) => ({
        id: m.id,
        senderId: m.sender_id,
        text: m.content,
        timestamp: formatTimestamp(m.created_at),
        isMine: m.sender_id === user?.id,
      }));
      setMessages(prev => ({
        ...prev,
        [conversationId]: mapped,
      }));
    } catch (err) {
      setErrorMessages(err instanceof Error ? err.message : 'Failed to load messages');
    } finally {
      setLoadingMessages(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation);
    }
  }, [selectedConversation, fetchMessages]);

  const filteredConversations = conversations.filter(c =>
    c.participantName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const currentMessages = selectedConversation ? (messages[selectedConversation] || []) : [];
  const currentConversation = conversations.find(c => c.id === selectedConversation);

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedConversation || !currentConversation) return;

    setSendingMessage(true);
    try {
      const response = await socialService.sendMessage(currentConversation.otherUserId, messageInput.trim());

      const newMessage: Message = {
        id: response.message.id,
        senderId: response.message.sender_id,
        text: response.message.content,
        timestamp: formatTimestamp(response.message.created_at),
        isMine: true,
      };

      setMessages(prev => ({
        ...prev,
        [selectedConversation]: [...(prev[selectedConversation] || []), newMessage],
      }));

      // Update last message in conversation list
      setConversations(prev => prev.map(c =>
        c.id === selectedConversation
          ? { ...c, lastMessage: messageInput.trim(), lastMessageTime: 'just now' }
          : c
      ));

      setMessageInput('');
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isAuthenticated()) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
          <MessageSquare className="text-blue-500" />
          Messages
        </h1>
        <div className="text-center py-12">
          <LogIn size={48} className="mx-auto mb-3 text-zinc-400" />
          <p className="text-zinc-500 mb-4">Please log in to view your messages.</p>
          <Button variant="default" onClick={() => window.location.href = '/login'}>
            Log In
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <MessageSquare className="text-blue-500" />
        Messages
      </h1>

      <Card className="overflow-hidden">
        <div className="flex h-[600px]">
          {/* Left Sidebar: Conversation List */}
          <div className="w-80 border-r border-zinc-200 dark:border-zinc-700 flex flex-col">
            {/* Search */}
            <div className="p-3 border-b border-zinc-200 dark:border-zinc-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={16} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search conversations..."
                  className="w-full pl-10 pr-4 py-2 text-sm border rounded-lg dark:bg-zinc-800 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto">
              {loadingConversations ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="animate-spin text-blue-500" size={24} />
                </div>
              ) : errorConversations ? (
                <div className="p-4 text-center">
                  <AlertCircle size={24} className="mx-auto mb-2 text-red-400" />
                  <p className="text-xs text-red-500 mb-2">{errorConversations}</p>
                  <Button variant="outline" size="sm" onClick={fetchConversations}>
                    Retry
                  </Button>
                </div>
              ) : filteredConversations.length === 0 ? (
                <div className="p-4 text-center text-zinc-500 text-sm">
                  {searchQuery ? 'No matching conversations.' : 'No conversations yet.'}
                </div>
              ) : (
                filteredConversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    onClick={() => setSelectedConversation(conversation.id)}
                    className={`w-full flex items-start gap-3 p-3 text-left hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors ${
                      selectedConversation === conversation.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                  >
                    {/* Avatar */}
                    <div className="relative flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-medium text-sm">
                        {conversation.participantName.charAt(0).toUpperCase()}
                      </div>
                      {conversation.isOnline && (
                        <Circle size={10} className="absolute bottom-0 right-0 text-green-500 fill-green-500" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm truncate">{conversation.participantName}</span>
                        <span className="text-[10px] text-zinc-400 flex-shrink-0">{conversation.lastMessageTime}</span>
                      </div>
                      <p className="text-xs text-zinc-500 truncate mt-0.5">{conversation.lastMessage}</p>
                    </div>

                    {conversation.unreadCount > 0 && (
                      <span className="flex-shrink-0 w-5 h-5 bg-blue-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                        {conversation.unreadCount}
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Right Panel: Message Thread */}
          <div className="flex-1 flex flex-col">
            {selectedConversation && currentConversation ? (
              <>
                {/* Thread Header */}
                <div className="flex items-center gap-3 p-4 border-b border-zinc-200 dark:border-zinc-700">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-medium text-sm">
                    {currentConversation.participantName.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-medium text-sm">{currentConversation.participantName}</h3>
                    <span className={`text-xs ${currentConversation.isOnline ? 'text-green-500' : 'text-zinc-400'}`}>
                      {currentConversation.isOnline ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {loadingMessages ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="animate-spin text-blue-500" size={24} />
                    </div>
                  ) : errorMessages ? (
                    <div className="text-center py-12">
                      <AlertCircle size={24} className="mx-auto mb-2 text-red-400" />
                      <p className="text-xs text-red-500 mb-2">{errorMessages}</p>
                      <Button variant="outline" size="sm" onClick={() => fetchMessages(selectedConversation)}>
                        Retry
                      </Button>
                    </div>
                  ) : currentMessages.length === 0 ? (
                    <div className="text-center py-12 text-zinc-400 text-sm">
                      No messages yet. Start the conversation!
                    </div>
                  ) : (
                    currentMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.isMine ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[70%] px-3 py-2 rounded-2xl text-sm ${
                            message.isMine
                              ? 'bg-blue-500 text-white rounded-br-md'
                              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-bl-md'
                          }`}
                        >
                          <p>{message.text}</p>
                          <span className={`text-[10px] mt-1 block ${message.isMine ? 'text-blue-100' : 'text-zinc-400'}`}>
                            {message.timestamp}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Message Input */}
                <div className="p-4 border-t border-zinc-200 dark:border-zinc-700">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Type a message..."
                      disabled={sendingMessage}
                      className="flex-1 px-4 py-2 text-sm border rounded-full dark:bg-zinc-800 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    />
                    <Button
                      size="icon"
                      className="rounded-full"
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim() || sendingMessage}
                    >
                      {sendingMessage ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <Send size={16} />
                      )}
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-400">
                <div className="text-center">
                  <MessageSquare size={48} className="mx-auto mb-2 opacity-50" />
                  <p>Select a conversation to start messaging</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
