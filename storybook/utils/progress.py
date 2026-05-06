from django.core.cache import cache

class ProgressTracker:
    TIMEOUT = 3600
    
    @classmethod
    def _get_key(cls, user):
        return f'progress_{user.id}'
    
    @classmethod
    def create(cls, user, activity_type):
        key = cls._get_key(user)
        cache.set(key, {
            'type': activity_type,
            'message': 'Starting...',
            'completed': False,
            'data': {}
        }, timeout=cls.TIMEOUT)
        return key
    
    @classmethod
    def update(cls, user, message, **extra_data):
        key = cls._get_key(user)
        data = cache.get(key)
        
        if not data:
            data = {
                'type': 'unknown',
                'message': message,
                'completed': False,
                'data': {}
            }
        
        data['message'] = message
        if extra_data:
            data['data'].update(extra_data)
        
        cache.set(key, data, timeout=cls.TIMEOUT)
    
    @classmethod
    def complete(cls, user, message='Completed'):
        key = cls._get_key(user)
        data = cache.get(key)
        if data:
            data['message'] = message
            data['completed'] = True
            cache.set(key, data, timeout=60)
    
    @classmethod
    def fail(cls, user, message='Failed'):
        key = cls._get_key(user)
        data = cache.get(key)
        if data:
            data['message'] = message
            data['completed'] = True
            cache.set(key, data, timeout=60)
    
    @classmethod
    def get(cls, user):
        key = cls._get_key(user)
        return cache.get(key)
    
    @classmethod
    def clear(cls, user):
        key = cls._get_key(user)
        cache.delete(key)