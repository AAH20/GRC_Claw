'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface User {
  id: string;
  name: string;
  avatar: string;
  status: 'online' | 'away' | 'offline';
}

interface Channel {
  id: string;
  name: string;
  type: 'channel' | 'dm';
  unreadCount: number;
  lastMessage?: string;
  lastMessageTime?: string;
  members?: User[];
  description?: string;
}

interface Message {
  id: string;
  channelId: string;
  author: User;
  content: string;
  timestamp: string;
  edited?: boolean;
  reactions?: { emoji: string; count: number; reacted: boolean }[];
}

interface DirectMessageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectUser: (user: User) => void;
  users: User[];
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_USERS: User[] = [
  { id: 'u1', name: 'Ahmed Hassan', avatar: '/avatars/ahmed.png', status: 'online' },
  { id: 'u2', name: 'Sarah Chen', avatar: '/avatars/sarah.png', status: 'online' },
  { id: 'u3', name: 'Marcus Johnson', avatar: '/avatars/marcus.png', status: 'away' },
  { id: 'u4', name: 'Priya Patel', avatar: '/avatars/priya.png', status: 'offline' },
  { id: 'u5', name: 'David Kim', avatar: '/avatars/david.png', status: 'online' },
  { id: 'u6', name: 'Elena Rodriguez', avatar: '/avatars/elena.png', status: 'away' },
];

const MOCK_CHANNELS: Channel[] = [
  { id: 'c1', name: 'general', type: 'channel', unreadCount: 3, lastMessage: 'Welcome to the community!', lastMessageTime: '2m ago', description: 'General discussion for all members' },
  { id: 'c2', name: 'announcements', type: 'channel', unreadCount: 0, lastMessage: 'New feature release v2.0', lastMessageTime: '1h ago', description: 'Official announcements' },
  { id: 'c3', name: 'help', type: 'channel', unreadCount: 1, lastMessage: 'How do I reset my password?', lastMessageTime: '30m ago', description: 'Get help from the community' },
  { id: 'c4', name: 'random', type: 'channel', unreadCount: 0, lastMessage: 'Check out this article', lastMessageTime: '3h ago', description: 'Off-topic conversations' },
  { id: 'dm1', name: 'Sarah Chen', type: 'dm', unreadCount: 2, lastMessage: 'Hey, are you coming to the meeting?', lastMessageTime: '5m ago', members: [MOCK_USERS[0], MOCK_USERS[1]] },
  { id: 'dm2', name: 'Marcus Johnson', type: 'dm', unreadCount: 0, lastMessage: 'Thanks for the update!', lastMessageTime: '1d ago', members: [MOCK_USERS[0], MOCK_USERS[2]] },
];

const MOCK_MESSAGES: Message[] = [
  { id: 'm1', channelId: 'c1', author: MOCK_USERS[1], content: 'Hey everyone! Welcome to the gated community. 🎉', timestamp: '10:00 AM', reactions: [{ emoji: '🎉', count: 5, reacted: true }, { emoji: '👋', count: 3, reacted: false }] },
  { id: 'm2', channelId: 'c1', author: MOCK_USERS[2], content: 'Thanks Sarah! Excited to be here.', timestamp: '10:02 AM' },
  { id: 'm3', channelId: 'c1', author: MOCK_USERS[4], content: 'Looking forward to collaborating with you all.', timestamp: '10:05 AM', reactions: [{ emoji: '👍', count: 2, reacted: false }] },
  { id: 'm4', channelId: 'c1', author: MOCK_USERS[0], content: 'Welcome aboard! Feel free to introduce yourselves.', timestamp: '10:08 AM' },
  { id: 'm5', channelId: 'c1', author: MOCK_USERS[5], content: 'Hi all! I\'m Elena, working on the frontend team.', timestamp: '10:12 AM' },
  { id: 'm6', channelId: 'c1', author: MOCK_USERS[1], content: 'Welcome Elena! We\'re glad to have you.', timestamp: '10:15 AM' },
  { id: 'm7', channelId: 'c1', author: MOCK_USERS[3], content: 'Hello everyone! Priya here, backend developer.', timestamp: '10:20 AM', reactions: [{ emoji: '👋', count: 4, reacted: true }] },
  { id: 'm8', channelId: 'c1', author: MOCK_USERS[2], content: 'Has anyone seen the new design specs?', timestamp: '10:25 AM' },
  { id: 'm9', channelId: 'c1', author: MOCK_USERS[4], content: 'Yes! They look amazing. Great work on the UI.', timestamp: '10:30 AM' },
  { id: 'm10', channelId: 'c1', author: MOCK_USERS[0], content: 'I\'ll share the link in a moment.', timestamp: '10:32 AM' },
];

// ─── Utility ─────────────────────────────────────────────────────────────────

function formatTime(timestamp: string): string {
  return timestamp;
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// ─── Status Indicator ────────────────────────────────────────────────────────

function StatusDot({ status }: { status: User['status'] }) {
  const colorMap = {
    online: 'bg-green-500',
    away: 'bg-yellow-500',
    offline: 'bg-gray-400',
  };
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${colorMap[status]} ring-2 ring-white`} />;
}

// ─── Channel List ────────────────────────────────────────────────────────────

interface ChannelListProps {
  channels: Channel[];
  activeChannelId: string;
  onSelectChannel: (channelId: string) => void;
  onNewDM: () => void;
  currentUser: User;
}

function ChannelList({ channels, activeChannelId, onSelectChannel, onNewDM, currentUser }: ChannelListProps) {
  const regularChannels = channels.filter((c) => c.type === 'channel');
  const dmChannels = channels.filter((c) => c.type === 'dm');

  return (
    <aside className="w-full md:w-72 lg:w-80 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-white">Messages</h1>
          <button
            onClick={onNewDM}
            className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            aria-label="New direct message"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
        {/* Current user */}
        <div className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm font-semibold">
              {getInitials(currentUser.name)}
            </div>
            <div className="absolute -bottom-0.5 -right-0.5">
              <StatusDot status={currentUser.status} />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{currentUser.name}</p>
            <p className="text-xs text-gray-400 capitalize">{currentUser.status}</p>
          </div>
        </div>
      </div>

      {/* Channel list */}
      <div className="flex-1 overflow-y-auto py-2">
        {/* Channels */}
        <div className="px-3 mb-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">Channels</p>
        </div>
        {regularChannels.map((channel) => (
          <button
            key={channel.id}
            onClick={() => onSelectChannel(channel.id)}
            className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors ${
              activeChannelId === channel.id
                ? 'bg-indigo-600/20 text-white border-r-2 border-indigo-500'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
            }`}
          >
            <span className="text-gray-500 text-lg">#</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{channel.name}</p>
              {channel.lastMessage && (
                <p className="text-xs text-gray-500 truncate">{channel.lastMessage}</p>
              )}
            </div>
            {channel.unreadCount > 0 && (
              <span className="bg-indigo-600 text-white text-xs font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center">
                {channel.unreadCount}
              </span>
            )}
          </button>
        ))}

        {/* Direct Messages */}
        <div className="px-3 mt-4 mb-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">Direct Messages</p>
        </div>
        {dmChannels.map((channel) => {
          const otherUser = channel.members?.find((m) => m.id !== currentUser.id);
          return (
            <button
              key={channel.id}
              onClick={() => onSelectChannel(channel.id)}
              className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors ${
                activeChannelId === channel.id
                  ? 'bg-indigo-600/20 text-white border-r-2 border-indigo-500'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              <div className="relative flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-300">
                  {otherUser ? getInitials(otherUser.name) : '?'}
                </div>
                {otherUser && (
                  <div className="absolute -bottom-0.5 -right-0.5">
                    <StatusDot status={otherUser.status} />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{channel.name}</p>
                {channel.lastMessage && (
                  <p className="text-xs text-gray-500 truncate">{channel.lastMessage}</p>
                )}
              </div>
              {channel.unreadCount > 0 && (
                <span className="bg-indigo-600 text-white text-xs font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center">
                  {channel.unreadCount}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </aside>
  );
}

// ─── Message Thread ─────────────────────────────────────────────────────────

interface MessageThreadProps {
  messages: Message[];
  activeChannel: Channel | undefined;
  currentUser: User;
  onReact: (messageId: string, emoji: string) => void;
}

function MessageThread({ messages, activeChannel, currentUser, onReact }: MessageThreadProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!activeChannel) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p className="text-gray-500 text-lg">Select a channel to start messaging</p>
        </div>
      </div>
    );
  }

  const channelMessages = messages.filter((m) => m.channelId === activeChannel.id);

  return (
    <div className="flex-1 flex flex-col bg-gray-950 min-w-0">
      {/* Channel header */}
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm flex items-center gap-3">
        {activeChannel.type === 'channel' ? (
          <>
            <span className="text-gray-500 text-xl">#</span>
            <div>
              <h2 className="text-white font-semibold">{activeChannel.name}</h2>
              {activeChannel.description && (
                <p className="text-xs text-gray-500">{activeChannel.description}</p>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="relative">
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-300">
                {getInitials(activeChannel.name)}
              </div>
            </div>
            <div>
              <h2 className="text-white font-semibold">{activeChannel.name}</h2>
              <p className="text-xs text-gray-500">Direct message</p>
            </div>
          </>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {channelMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-600">No messages yet. Be the first to say something!</p>
          </div>
        ) : (
          channelMessages.map((message, index) => {
            const isOwn = message.author.id === currentUser.id;
            const showAvatar =
              index === 0 || channelMessages[index - 1].author.id !== message.author.id;

            return (
              <div key={message.id} className={`group flex gap-3 ${isOwn ? 'flex-row-reverse' : ''}`}>
                {showAvatar ? (
                  <div className="flex-shrink-0">
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold ${
                      isOwn ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300'
                    }`}>
                      {getInitials(message.author.name)}
                    </div>
                  </div>
                ) : (
                  <div className="w-9 flex-shrink-0" />
                )}
                <div className={`flex flex-col max-w-[75%] ${isOwn ? 'items-end' : 'items-start'}`}>
                  {showAvatar && (
                    <div className={`flex items-baseline gap-2 mb-1 ${isOwn ? 'flex-row-reverse' : ''}`}>
                      <span className="text-sm font-medium text-gray-300">{message.author.name}</span>
                      <span className="text-xs text-gray-600">{formatTime(message.timestamp)}</span>
                    </div>
                  )}
                  <div className={`relative px-4 py-2.5 rounded-2xl ${
                    isOwn
                      ? 'bg-indigo-600 text-white rounded-br-md'
                      : 'bg-gray-800 text-gray-200 rounded-bl-md'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                    {message.edited && (
                      <span className="text-xs opacity-60 ml-1">(edited)</span>
                    )}
                  </div>
                  {/* Reactions */}
                  {message.reactions && message.reactions.length > 0 && (
                    <div className={`flex gap-1 mt-1 ${isOwn ? 'justify-end' : 'justify-start'}`}>
                      {message.reactions.map((reaction, rIdx) => (
                        <button
                          key={rIdx}
                          onClick={() => onReact(message.id, reaction.emoji)}
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs transition-colors ${
                            reaction.reacted
                              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/50'
                              : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <span>{reaction.emoji}</span>
                          <span>{reaction.count}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

// ─── Message Composer ────────────────────────────────────────────────────────

interface MessageComposerProps {
  onSend: (content: string) => void;
  placeholder?: string;
}

function MessageComposer({ onSend, placeholder = 'Type a message...' }: MessageComposerProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = content.trim();
      if (!trimmed) return;
      onSend(trimmed);
      setContent('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    },
    [content, onSend]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    },
    [handleSubmit]
  );

  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
  }, []);

  return (
    <div className="px-4 py-3 border-t border-gray-800 bg-gray-900/80 backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className="w-full resize-none rounded-xl bg-gray-800 text-gray-200 placeholder-gray-500 px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 border border-gray-700 max-h-[150px]"
          />
          <button
            type="button"
            className="absolute right-3 bottom-3 text-gray-500 hover:text-gray-300 transition-colors"
            aria-label="Add emoji"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
        <button
          type="submit"
          disabled={!content.trim()}
          className="flex-shrink-0 p-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
          aria-label="Send message"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </form>
    </div>
  );
}

// ─── Direct Message Modal ────────────────────────────────────────────────────

function DirectMessageModal({ isOpen, onClose, onSelectUser, users }: DirectMessageModalProps) {
  const [search, setSearch] = useState('');

  const filteredUsers = users.filter(
    (u) => u.name.toLowerCase().includes(search.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">New Message</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-800">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search people..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-gray-800 text-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 border border-gray-700"
              autoFocus
            />
          </div>
        </div>

        {/* User list */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredUsers.length === 0 ? (
            <p className="text-center text-gray-500 py-8 text-sm">No users found</p>
          ) : (
            filteredUsers.map((user) => (
              <button
                key={user.id}
                onClick={() => onSelectUser(user)}
                className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-800 transition-colors text-left"
              >
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-sm font-semibold text-gray-300">
                    {getInitials(user.name)}
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5">
                    <StatusDot status={user.status} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{user.name}</p>
                  <p className="text-xs text-gray-500 capitalize">{user.status}</p>
                </div>
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function MessagesPage() {
  const [channels, setChannels] = useState<Channel[]>(MOCK_CHANNELS);
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [activeChannelId, setActiveChannelId] = useState<string>('c1');
  const [isDMModalOpen, setIsDMModalOpen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const currentUser = MOCK_USERS[0];
  const activeChannel = channels.find((c) => c.id === activeChannelId);

  const handleSelectChannel = useCallback((channelId: string) => {
    setActiveChannelId(channelId);
    // Clear unread
    setChannels((prev) =>
      prev.map((c) => (c.id === channelId ? { ...c, unreadCount: 0 } : c))
    );
    // On mobile, hide sidebar after selection
    if (window.innerWidth < 768) {
      setShowSidebar(false);
    }
  }, []);

  const handleSend = useCallback(
    (content: string) => {
      const newMessage: Message = {
        id: `m${Date.now()}`,
        channelId: activeChannelId,
        author: currentUser,
        content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, newMessage]);
      // Update channel last message
      setChannels((prev) =>
        prev.map((c) =>
          c.id === activeChannelId
            ? { ...c, lastMessage: content, lastMessageTime: 'Just now' }
            : c
        )
      );
    },
    [activeChannelId, currentUser]
  );

  const handleReact = useCallback((messageId: string, emoji: string) => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== messageId) return m;
        const reactions = m.reactions ? [...m.reactions] : [];
        const existing = reactions.find((r) => r.emoji === emoji);
        if (existing) {
          if (existing.reacted) {
            existing.count -= 1;
            existing.reacted = false;
            if (existing.count <= 0) {
              return { ...m, reactions: reactions.filter((r) => r.emoji !== emoji) };
            }
          } else {
            existing.count += 1;
            existing.reacted = true;
          }
        } else {
          reactions.push({ emoji, count: 1, reacted: true });
        }
        return { ...m, reactions };
      })
    );
  }, []);

  const handleNewDM = useCallback(() => {
    setIsDMModalOpen(true);
  }, []);

  const handleSelectUser = useCallback(
    (user: User) => {
      // Check if DM already exists
      const existingDM = channels.find(
        (c) => c.type === 'dm' && c.members?.some((m) => m.id === user.id)
      );
      if (existingDM) {
        handleSelectChannel(existingDM.id);
      } else {
        const newChannel: Channel = {
          id: `dm_${Date.now()}`,
          name: user.name,
          type: 'dm',
          unreadCount: 0,
          members: [currentUser, user],
        };
        setChannels((prev) => [...prev, newChannel]);
        setActiveChannelId(newChannel.id);
      }
      setIsDMModalOpen(false);
    },
    [channels, currentUser, handleSelectChannel]
  );

  return (
    <div className="h-screen w-full flex bg-gray-950 text-gray-100 overflow-hidden">
      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-gray-800 text-white shadow-lg"
        aria-label="Toggle sidebar"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <div
        className={`${
          showSidebar ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 fixed md:relative z-30 h-full transition-transform duration-200 ease-in-out`}
      >
        <ChannelList
          channels={channels}
          activeChannelId={activeChannelId}
          onSelectChannel={handleSelectChannel}
          onNewDM={handleNewDM}
          currentUser={currentUser}
        />
      </div>

      {/* Overlay for mobile sidebar */}
      {showSidebar && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-20"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <MessageThread
          messages={messages}
          activeChannel={activeChannel}
          currentUser={currentUser}
          onReact={handleReact}
        />
        <MessageComposer
          onSend={handleSend}
          placeholder={
            activeChannel
              ? `Message ${activeChannel.type === 'channel' ? '#' : ''}${activeChannel.name}`
              : 'Select a channel'
          }
        />
      </div>

      {/* DM Modal */}
      <DirectMessageModal
        isOpen={isDMModalOpen}
        onClose={() => setIsDMModalOpen(false)}
        onSelectUser={handleSelectUser}
        users={MOCK_USERS.filter((u) => u.id !== currentUser.id)}
      />
    </div>
  );
}
