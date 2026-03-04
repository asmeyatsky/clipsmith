'use client';

import { useState, useEffect, useCallback } from 'react';
import { Users, Calendar, Circle, UserPlus, MapPin, Clock, Loader2, AlertCircle, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { communityService, Group as APIGroup, CommunityEvent as APIEvent, Circle as APICircle } from '@/lib/api/community';
import { useAuthStore } from '@/lib/auth/auth-store';

interface Group {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  category: string;
  isJoined: boolean;
}

interface Event {
  id: string;
  title: string;
  description: string;
  date: string;
  location: string;
  attendeeCount: number;
  isRsvped: boolean;
}

interface CreatorCircle {
  id: string;
  name: string;
  creatorCount: number;
  description: string;
}

export default function CommunityPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [groups, setGroups] = useState<Group[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [circles, setCircles] = useState<CreatorCircle[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadingCircles, setLoadingCircles] = useState(true);
  const [errorGroups, setErrorGroups] = useState<string | null>(null);
  const [errorEvents, setErrorEvents] = useState<string | null>(null);
  const [errorCircles, setErrorCircles] = useState<string | null>(null);
  const [joiningGroup, setJoiningGroup] = useState<string | null>(null);
  const [rsvpingEvent, setRsvpingEvent] = useState<string | null>(null);

  const fetchGroups = useCallback(async () => {
    setLoadingGroups(true);
    setErrorGroups(null);
    try {
      const response = await communityService.listGroups();
      setGroups(
        response.groups.map((g: APIGroup) => ({
          id: g.id,
          name: g.name,
          description: g.description,
          memberCount: 0,
          category: g.is_public ? 'Public' : 'Private',
          isJoined: false,
        }))
      );
    } catch (err) {
      setErrorGroups(err instanceof Error ? err.message : 'Failed to load groups');
    } finally {
      setLoadingGroups(false);
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    setLoadingEvents(true);
    setErrorEvents(null);
    try {
      const response = await communityService.listEvents();
      setEvents(
        response.events.map((e: APIEvent) => ({
          id: e.id,
          title: e.title,
          description: e.description,
          date: e.start_time,
          location: e.location || 'Virtual',
          attendeeCount: 0,
          isRsvped: false,
        }))
      );
    } catch (err) {
      setErrorEvents(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoadingEvents(false);
    }
  }, []);

  const fetchCircles = useCallback(async () => {
    if (!isAuthenticated()) {
      setLoadingCircles(false);
      return;
    }
    setLoadingCircles(true);
    setErrorCircles(null);
    try {
      const response = await communityService.listCircles();
      setCircles(
        response.circles.map((c: APICircle) => ({
          id: c.id,
          name: c.name,
          creatorCount: 0,
          description: c.description,
        }))
      );
    } catch (err) {
      setErrorCircles(err instanceof Error ? err.message : 'Failed to load circles');
    } finally {
      setLoadingCircles(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchGroups();
    fetchEvents();
    fetchCircles();
  }, [fetchGroups, fetchEvents, fetchCircles]);

  const toggleJoinGroup = async (groupId: string) => {
    if (!isAuthenticated()) return;

    const group = groups.find(g => g.id === groupId);
    if (!group) return;

    setJoiningGroup(groupId);
    try {
      if (group.isJoined) {
        await communityService.leaveGroup(groupId);
      } else {
        await communityService.joinGroup(groupId);
      }
      setGroups(prev => prev.map(g =>
        g.id === groupId ? { ...g, isJoined: !g.isJoined, memberCount: g.isJoined ? g.memberCount - 1 : g.memberCount + 1 } : g
      ));
    } catch (err) {
      console.error('Failed to toggle group membership:', err);
    } finally {
      setJoiningGroup(null);
    }
  };

  const toggleRsvp = async (eventId: string) => {
    if (!isAuthenticated()) return;

    const event = events.find(e => e.id === eventId);
    if (!event) return;

    setRsvpingEvent(eventId);
    try {
      const rsvpStatus = event.isRsvped ? 'not_attending' : 'attending';
      await communityService.rsvpEvent(eventId, rsvpStatus);
      setEvents(prev => prev.map(e =>
        e.id === eventId ? { ...e, isRsvped: !e.isRsvped, attendeeCount: e.isRsvped ? e.attendeeCount - 1 : e.attendeeCount + 1 } : e
      ));
    } catch (err) {
      console.error('Failed to toggle RSVP:', err);
    } finally {
      setRsvpingEvent(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });
  };

  const renderAuthPrompt = () => (
    <div className="text-center py-12">
      <LogIn size={48} className="mx-auto mb-3 text-zinc-400" />
      <p className="text-zinc-500 mb-4">Please log in to access this feature.</p>
      <Button variant="default" onClick={() => window.location.href = '/login'}>
        Log In
      </Button>
    </div>
  );

  const renderError = (error: string, onRetry: () => void) => (
    <div className="text-center py-12">
      <AlertCircle size={48} className="mx-auto mb-3 text-red-400" />
      <p className="text-red-500 mb-4">{error}</p>
      <Button variant="outline" onClick={onRetry}>
        Try Again
      </Button>
    </div>
  );

  const renderLoading = () => (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="animate-spin text-blue-500" size={32} />
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <Users className="text-blue-500" />
        Community
      </h1>

      <Tabs defaultValue="groups">
        <TabsList className="mb-6">
          <TabsTrigger value="groups">Groups</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="circles">Circles</TabsTrigger>
        </TabsList>

        <TabsContent value="groups">
          {loadingGroups ? renderLoading() : errorGroups ? renderError(errorGroups, fetchGroups) : (
            <>
              {groups.length === 0 ? (
                <div className="text-center py-12 text-zinc-500">
                  No groups available yet. Be the first to create one!
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {groups.map((group) => (
                    <Card key={group.id}>
                      <CardHeader>
                        <CardTitle className="text-lg">{group.name}</CardTitle>
                        <CardDescription>{group.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1 text-sm text-zinc-500">
                            <Users size={14} />
                            <span>{group.memberCount.toLocaleString()} members</span>
                          </div>
                          <Button
                            variant={group.isJoined ? 'secondary' : 'default'}
                            size="sm"
                            onClick={() => toggleJoinGroup(group.id)}
                            disabled={joiningGroup === group.id || !isAuthenticated()}
                            className="gap-1"
                          >
                            {joiningGroup === group.id ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <UserPlus size={14} />
                            )}
                            {group.isJoined ? 'Joined' : 'Join'}
                          </Button>
                        </div>
                        <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                          {group.category}
                        </span>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="events">
          {loadingEvents ? renderLoading() : errorEvents ? renderError(errorEvents, fetchEvents) : (
            <>
              {events.length === 0 ? (
                <div className="text-center py-12 text-zinc-500">
                  No upcoming events. Check back later!
                </div>
              ) : (
                <div className="space-y-4">
                  {events.map((event) => (
                    <Card key={event.id}>
                      <CardContent className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-6">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{event.title}</h3>
                          <p className="text-sm text-zinc-500 mt-1">{event.description}</p>
                          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-zinc-400">
                            <span className="flex items-center gap-1">
                              <Clock size={14} />
                              {formatDate(event.date)}
                            </span>
                            <span className="flex items-center gap-1">
                              <MapPin size={14} />
                              {event.location}
                            </span>
                            <span className="flex items-center gap-1">
                              <Users size={14} />
                              {event.attendeeCount} attending
                            </span>
                          </div>
                        </div>
                        <Button
                          variant={event.isRsvped ? 'secondary' : 'default'}
                          onClick={() => toggleRsvp(event.id)}
                          disabled={rsvpingEvent === event.id || !isAuthenticated()}
                        >
                          {rsvpingEvent === event.id ? (
                            <Loader2 size={16} className="animate-spin mr-2" />
                          ) : null}
                          {event.isRsvped ? 'Cancel RSVP' : 'RSVP'}
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="circles">
          {!isAuthenticated() ? renderAuthPrompt() : (
            <>
              {loadingCircles ? renderLoading() : errorCircles ? renderError(errorCircles, fetchCircles) : (
                <>
                  <div className="mb-6">
                    <p className="text-zinc-500 mb-4">Organize the creators you follow into circles for a personalized feed experience.</p>
                    <Button variant="default" className="gap-1">
                      <Circle size={14} />
                      Create New Circle
                    </Button>
                  </div>
                  {circles.length === 0 ? (
                    <div className="text-center py-12 text-zinc-500">
                      You have not created any circles yet. Create one to get started!
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {circles.map((circle) => (
                        <Card key={circle.id}>
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <Circle size={16} className="text-blue-500" />
                              {circle.name}
                            </CardTitle>
                            <CardDescription>{circle.description}</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-zinc-500">{circle.creatorCount} creators</span>
                              <Button variant="ghost" size="sm">
                                View
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
