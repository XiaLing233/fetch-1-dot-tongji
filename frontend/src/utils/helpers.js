export function get_csrf_token(cookie) {
    try {
        return cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1];
    }
    catch (error) {
        throw new Error({
            message: 'CSRF token not found in cookie'
        });
    }
}