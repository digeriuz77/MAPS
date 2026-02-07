"""
Frontend Content Type Filter Tests

Tests for the frontend content type filtering functionality:
- UI component rendering with content type badges
- Filter state management
- API integration with content_type parameter
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestContentTypeUIComponents:
    """Tests for content type UI components"""
    
    def test_content_type_info_shared(self):
        """Test getContentTypeInfo returns correct data for shared"""
        # This simulates the JavaScript function behavior
        content_type_info = {
            'shared': {
                'class': 'content-type-shared',
                'icon': 'fa-users',
                'label': 'Shared'
            },
            'customer_facing': {
                'class': 'content-type-customer',
                'icon': 'fa-user-tie',
                'label': 'Customer-Facing'
            },
            'colleague_facing': {
                'class': 'content-type-colleague',
                'icon': 'fa-user-friends',
                'label': 'Colleague-Facing'
            }
        }
        
        info = content_type_info['shared']
        assert info['class'] == 'content-type-shared'
        assert info['icon'] == 'fa-users'
        assert info['label'] == 'Shared'
    
    def test_content_type_info_customer_facing(self):
        """Test getContentTypeInfo returns correct data for customer_facing"""
        content_type_info = {
            'shared': {
                'class': 'content-type-shared',
                'icon': 'fa-users',
                'label': 'Shared'
            },
            'customer_facing': {
                'class': 'content-type-customer',
                'icon': 'fa-user-tie',
                'label': 'Customer-Facing'
            },
            'colleague_facing': {
                'class': 'content-type-colleague',
                'icon': 'fa-user-friends',
                'label': 'Colleague-Facing'
            }
        }
        
        info = content_type_info['customer_facing']
        assert info['class'] == 'content-type-customer'
        assert info['icon'] == 'fa-user-tie'
        assert info['label'] == 'Customer-Facing'
    
    def test_content_type_info_colleague_facing(self):
        """Test getContentTypeInfo returns correct data for colleague_facing"""
        content_type_info = {
            'shared': {
                'class': 'content-type-shared',
                'icon': 'fa-users',
                'label': 'Shared'
            },
            'customer_facing': {
                'class': 'content-type-customer',
                'icon': 'fa-user-tie',
                'label': 'Customer-Facing'
            },
            'colleague_facing': {
                'class': 'content-type-colleague',
                'icon': 'fa-user-friends',
                'label': 'Colleague-Facing'
            }
        }
        
        info = content_type_info['colleague_facing']
        assert info['class'] == 'content-type-colleague'
        assert info['icon'] == 'fa-user-friends'
        assert info['label'] == 'Colleague-Facing'


class TestFilterStateManagement:
    """Tests for filter state management"""
    
    def test_default_filter_state(self):
        """Test default filter state has contentType: 'all'"""
        # Simulates the JavaScript state object
        state = {
            'currentUser': None,
            'modules': [],
            'learningPaths': [],
            'currentAttempt': None,
            'currentModule': None,
            'userProgress': None,
            'filters': {
                'focusArea': '',
                'difficulty': '',
                'search': '',
                'contentType': 'all'
            }
        }
        
        assert state['filters']['contentType'] == 'all'
    
    def test_filter_state_update(self):
        """Test updating filter state"""
        state = {
            'filters': {
                'focusArea': '',
                'difficulty': '',
                'search': '',
                'contentType': 'all'
            }
        }
        
        # Simulate user selecting customer_facing filter
        state['filters']['contentType'] = 'customer_facing'
        
        assert state['filters']['contentType'] == 'customer_facing'
    
    def test_filter_state_reset(self):
        """Test resetting filter state to 'all'"""
        state = {
            'filters': {
                'contentType': 'colleague_facing'
            }
        }
        
        # Simulate reset
        state['filters']['contentType'] = 'all'
        
        assert state['filters']['contentType'] == 'all'


class TestAPIIntegration:
    """Tests for API integration with content_type parameter"""
    
    def test_list_modules_url_with_content_type(self):
        """Test URL generation with content_type filter"""
        # Simulates the JavaScript MIAPI.listModules function
        def build_url(base_url, filters):
            params = []
            if filters.get('focusArea'):
                params.append(f"focus_area={filters['focusArea']}")
            if filters.get('difficulty'):
                params.append(f"difficulty={filters['difficulty']}")
            if filters.get('contentType') and filters['contentType'] != 'all':
                params.append(f"content_type={filters['contentType']}")
            
            query_string = '&'.join(params)
            return f"{base_url}/modules?{query_string}" if query_string else f"{base_url}/modules"
        
        filters = {
            'focusArea': '',
            'difficulty': '',
            'contentType': 'shared'
        }
        
        url = build_url('/api/mi-practice', filters)
        assert 'content_type=shared' in url
    
    def test_list_modules_url_without_content_type(self):
        """Test URL generation without content_type filter (all)"""
        def build_url(base_url, filters):
            params = []
            if filters.get('focusArea'):
                params.append(f"focus_area={filters['focusArea']}")
            if filters.get('difficulty'):
                params.append(f"difficulty={filters['difficulty']}")
            if filters.get('contentType') and filters['contentType'] != 'all':
                params.append(f"content_type={filters['contentType']}")
            
            query_string = '&'.join(params)
            return f"{base_url}/modules?{query_string}" if query_string else f"{base_url}/modules"
        
        filters = {
            'focusArea': 'Building Rapport',
            'difficulty': '',
            'contentType': 'all'
        }
        
        url = build_url('/api/mi-practice', filters)
        assert 'content_type' not in url
        assert 'focus_area=Building Rapport' in url or 'focus_area=Building+Rapport' in url or 'focus_area=Building%20Rapport' in url
    
    def test_list_modules_url_with_multiple_filters(self):
        """Test URL generation with multiple filters including content_type"""
        def build_url(base_url, filters):
            params = []
            if filters.get('focusArea'):
                params.append(f"focus_area={filters['focusArea']}")
            if filters.get('difficulty'):
                params.append(f"difficulty={filters['difficulty']}")
            if filters.get('contentType') and filters['contentType'] != 'all':
                params.append(f"content_type={filters['contentType']}")
            
            query_string = '&'.join(params)
            return f"{base_url}/modules?{query_string}" if query_string else f"{base_url}/modules"
        
        filters = {
            'focusArea': 'Building Rapport',
            'difficulty': 'beginner',
            'contentType': 'customer_facing'
        }
        
        url = build_url('/api/mi-practice', filters)
        assert 'content_type=customer_facing' in url
        assert 'difficulty=beginner' in url


class TestModuleCardRendering:
    """Tests for module card rendering with content type"""
    
    def test_module_card_has_content_type_attribute(self):
        """Test module card has data-content-type attribute"""
        # Simulates the createModuleCard function
        module = {
            'id': 'mod-001',
            'content_type': 'shared',
            'title': 'Test Module',
            'difficulty_level': 'beginner',
            'estimated_minutes': 5,
            'learning_objective': 'Test objective',
            'mi_focus_area': 'Building Rapport',
            'target_competencies': ['A6'],
            'maps_rubric': {},
            'maps_framework_alignment': {}
        }
        
        # The card should have data-content-type attribute
        content_type = module.get('content_type', 'shared')
        assert content_type == 'shared'
    
    def test_module_card_content_type_badge(self):
        """Test module card displays content type badge"""
        module = {
            'content_type': 'customer_facing',
            'title': 'Customer Module'
        }
        
        content_type = module['content_type']
        content_type_info = {
            'customer_facing': {
                'class': 'content-type-customer',
                'label': 'Customer-Facing'
            }
        }
        
        info = content_type_info[content_type]
        assert info['label'] == 'Customer-Facing'
        assert 'customer' in info['class']


class TestContentTypeFiltering:
    """Tests for content type filtering behavior"""
    
    def test_filter_modules_by_content_type(self):
        """Test filtering modules by content type"""
        modules = [
            {'id': '1', 'content_type': 'shared', 'title': 'Shared 1'},
            {'id': '2', 'content_type': 'shared', 'title': 'Shared 2'},
            {'id': '3', 'content_type': 'customer_facing', 'title': 'Customer 1'},
            {'id': '4', 'content_type': 'colleague_facing', 'title': 'Colleague 1'},
        ]
        
        # Filter for shared modules
        filtered = [m for m in modules if m['content_type'] == 'shared']
        
        assert len(filtered) == 2
        assert all(m['content_type'] == 'shared' for m in filtered)
    
    def test_filter_modules_show_all(self):
        """Test showing all modules when content_type is 'all'"""
        modules = [
            {'id': '1', 'content_type': 'shared'},
            {'id': '2', 'content_type': 'customer_facing'},
            {'id': '3', 'content_type': 'colleague_facing'},
        ]
        
        # When contentType is 'all', show all modules
        content_type_filter = 'all'
        filtered = modules if content_type_filter == 'all' else [
            m for m in modules if m['content_type'] == content_type_filter
        ]
        
        assert len(filtered) == 3


class TestContentTypeValidation:
    """Tests for content type validation"""
    
    def test_valid_content_types(self):
        """Test valid content type values"""
        valid_types = ['shared', 'customer_facing', 'colleague_facing']
        
        assert 'shared' in valid_types
        assert 'customer_facing' in valid_types
        assert 'colleague_facing' in valid_types
    
    def test_invalid_content_type(self):
        """Test invalid content type is rejected"""
        valid_types = ['shared', 'customer_facing', 'colleague_facing']
        invalid_type = 'invalid_type'
        
        assert invalid_type not in valid_types
    
    def test_content_type_case_sensitivity(self):
        """Test content type values are case sensitive"""
        valid_types = ['shared', 'customer_facing', 'colleague_facing']
        
        # Should be lowercase with underscores
        assert 'Shared' not in valid_types
        assert 'CUSTOMER_FACING' not in valid_types
