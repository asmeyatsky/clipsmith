'use client';

import { useState, useEffect, useCallback } from 'react';
import { GraduationCap, Star, Users, Filter, BookOpen, Clock, CheckCircle, Loader2, AlertCircle, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { courseService, Course as APICourse, EnrolledCourse } from '@/lib/api/courses';
import { useAuthStore } from '@/lib/auth/auth-store';

interface Course {
  id: string;
  title: string;
  creator: string;
  description: string;
  price: number;
  enrollmentCount: number;
  rating: number;
  category: string;
  duration: string;
  lessonCount: number;
  thumbnailUrl?: string;
  isEnrolled: boolean;
}

const courseCategories = ['all', 'editing', 'cinematography', 'storytelling', 'effects', 'audio', 'color', 'business', 'social-media', 'general'];

export default function CoursesPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [courses, setCourses] = useState<Course[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [errorCourses, setErrorCourses] = useState<string | null>(null);
  const [enrollingCourse, setEnrollingCourse] = useState<string | null>(null);
  const [enrolledIds, setEnrolledIds] = useState<Set<string>>(new Set());

  const fetchCourses = useCallback(async () => {
    setLoadingCourses(true);
    setErrorCourses(null);
    try {
      const [coursesResponse, enrolledResponse] = await Promise.all([
        courseService.listCourses(
          selectedCategory !== 'all' ? selectedCategory : undefined
        ),
        isAuthenticated()
          ? courseService.getEnrollments().catch(() => ({ success: true, courses: [] as EnrolledCourse[] }))
          : Promise.resolve({ success: true, courses: [] as EnrolledCourse[] }),
      ]);

      const enrolledSet = new Set(enrolledResponse.courses.map((e: EnrolledCourse) => e.id));
      setEnrolledIds(enrolledSet);

      setCourses(
        coursesResponse.courses.map((c: APICourse) => ({
          id: c.id,
          title: c.title,
          creator: c.creator_id,
          description: c.description,
          price: c.price,
          enrollmentCount: 0,
          rating: 0,
          category: c.category,
          duration: '',
          lessonCount: 0,
          isEnrolled: enrolledSet.has(c.id),
        }))
      );
    } catch (err) {
      setErrorCourses(err instanceof Error ? err.message : 'Failed to load courses');
    } finally {
      setLoadingCourses(false);
    }
  }, [selectedCategory, isAuthenticated]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleEnroll = async (courseId: string) => {
    if (!isAuthenticated()) return;

    setEnrollingCourse(courseId);
    try {
      await courseService.enrollInCourse(courseId);
      setCourses(prev => prev.map(c =>
        c.id === courseId ? { ...c, isEnrolled: true, enrollmentCount: c.enrollmentCount + 1 } : c
      ));
      setEnrolledIds(prev => new Set(prev).add(courseId));
    } catch (err) {
      console.error('Failed to enroll:', err);
    } finally {
      setEnrollingCourse(null);
    }
  };

  const enrolledCourses = courses.filter(c => c.isEnrolled);
  const filteredCourses = courses;

  const renderStars = (rating: number) => {
    if (rating === 0) return null;
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            size={12}
            className={star <= Math.round(rating) ? 'text-yellow-500 fill-yellow-500' : 'text-zinc-300'}
          />
        ))}
        <span className="text-xs text-zinc-500 ml-1">{rating}</span>
      </div>
    );
  };

  const renderLoading = () => (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="animate-spin text-blue-500" size={32} />
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

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <GraduationCap className="text-blue-500" />
        Courses & Tutorials
      </h1>

      {loadingCourses ? renderLoading() : errorCourses ? renderError(errorCourses, fetchCourses) : (
        <>
          {/* Enrolled Courses */}
          {enrolledCourses.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <BookOpen size={20} />
                Your Enrolled Courses
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {enrolledCourses.map((course) => (
                  <Card key={course.id} className="border-blue-200 dark:border-blue-800">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CheckCircle size={18} className="text-green-500 flex-shrink-0" />
                      </div>
                      <CardDescription>by {course.creator}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between text-sm text-zinc-500">
                        {course.duration && (
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {course.duration}
                          </span>
                        )}
                        {course.lessonCount > 0 && (
                          <span>{course.lessonCount} lessons</span>
                        )}
                      </div>
                      <Button variant="default" size="sm" className="w-full mt-3">
                        Continue Learning
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Category Filter */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Filter size={16} className="text-zinc-500" />
              <span className="text-sm font-medium">Filter by Category</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {courseCategories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                    selectedCategory === cat
                      ? 'bg-blue-500 text-white'
                      : 'bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  {cat === 'all' ? 'All Courses' : cat.charAt(0).toUpperCase() + cat.slice(1).replace('-', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Course Grid */}
          {filteredCourses.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              No courses found in this category.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredCourses.map((course) => (
                <Card key={course.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                  {/* Thumbnail Placeholder */}
                  <div className="h-36 bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center rounded-t-xl">
                    <GraduationCap size={32} className="text-blue-500/50" />
                  </div>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base line-clamp-2">{course.title}</CardTitle>
                    <CardDescription className="text-xs">by {course.creator}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-zinc-500 line-clamp-2 mb-3">{course.description}</p>
                    {renderStars(course.rating)}
                    <div className="flex items-center justify-between mt-3">
                      {course.enrollmentCount > 0 && (
                        <div className="flex items-center gap-1 text-xs text-zinc-400">
                          <Users size={12} />
                          <span>{course.enrollmentCount.toLocaleString()} enrolled</span>
                        </div>
                      )}
                      {course.duration && (
                        <span className="flex items-center gap-1 text-xs text-zinc-400">
                          <Clock size={12} />
                          {course.duration}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center justify-between mt-3">
                      <span className="font-bold text-sm">
                        {course.price === 0 ? (
                          <span className="text-green-500">Free</span>
                        ) : (
                          `$${course.price.toFixed(2)}`
                        )}
                      </span>
                      <Button
                        size="sm"
                        variant={course.isEnrolled ? 'secondary' : 'default'}
                        disabled={course.isEnrolled || enrollingCourse === course.id || !isAuthenticated()}
                        onClick={() => handleEnroll(course.id)}
                      >
                        {enrollingCourse === course.id ? (
                          <Loader2 size={14} className="animate-spin mr-1" />
                        ) : null}
                        {course.isEnrolled ? 'Enrolled' : 'Enroll'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
