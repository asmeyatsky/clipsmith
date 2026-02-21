import DOMPurify from 'dompurify';

export function sanitizeHtml(dirty: string): string {
    return DOMPurify.sanitize(dirty, {
        ALLOWED_TAGS: [],
        ALLOWED_ATTR: [],
    });
}

export function sanitizeForReact(dirty: string): string {
    return DOMPurify.sanitize(dirty);
}
