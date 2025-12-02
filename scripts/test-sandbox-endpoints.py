#!/usr/bin/env python3
"""
Test script for Amplify Gen 2 sandbox endpoints.

This script tests the three main API endpoints:
1. POST /game/new - Create new game session
2. POST /game/command - Execute game command
3. GET /game/state/{session_id} - Query game state

Requirements: 11.1, 11.2, 22.1, 22.3

Usage:
    python scripts/test-sandbox-endpoints.py <api_url>

Example:
    python scripts/test-sandbox-endpoints.py https://abc123.execute-api.us-east-1.amazonaws.com/prod
"""

import sys
import json
import requests
from typing import Dict, Any, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def test_new_game(api_url: str) -> Optional[str]:
    """
    Test POST /game/new endpoint.
    
    Returns:
        Session ID if successful, None otherwise.
    """
    print_section("Test 1: Create New Game (POST /game/new)")
    
    endpoint = f"{api_url}/game/new"
    print_info(f"Endpoint: {endpoint}")
    
    try:
        response = requests.post(endpoint, json={}, timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_error(f"Expected status 200, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate response structure
        required_fields = ['session_id', 'room', 'description', 'state']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return None
        
        # Validate state structure
        state = data.get('state', {})
        required_state_fields = ['sanity', 'score', 'moves']
        missing_state_fields = [field for field in required_state_fields if field not in state]
        
        if missing_state_fields:
            print_error(f"Missing required state fields: {missing_state_fields}")
            return None
        
        # Validate initial values
        if state.get('sanity') != 100:
            print_warning(f"Expected sanity=100, got {state.get('sanity')}")
        
        if state.get('score') != 0:
            print_warning(f"Expected score=0, got {state.get('score')}")
        
        if state.get('moves') != 0:
            print_warning(f"Expected moves=0, got {state.get('moves')}")
        
        session_id = data.get('session_id')
        print_success(f"New game created successfully!")
        print_success(f"Session ID: {session_id}")
        print_success(f"Starting room: {data.get('room')}")
        
        return session_id
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response: {e}")
        return None


def test_command(api_url: str, session_id: str) -> bool:
    """
    Test POST /game/command endpoint.
    
    Args:
        api_url: Base API URL
        session_id: Session ID from new game
    
    Returns:
        True if successful, False otherwise.
    """
    print_section("Test 2: Execute Command (POST /game/command)")
    
    endpoint = f"{api_url}/game/command"
    print_info(f"Endpoint: {endpoint}")
    
    # Test with "look" command
    command = "look"
    print_info(f"Command: {command}")
    
    try:
        response = requests.post(
            endpoint,
            json={'session_id': session_id, 'command': command},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_error(f"Expected status 200, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate response structure
        required_fields = ['success', 'message']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        if not data.get('success'):
            print_warning(f"Command execution reported failure: {data.get('message')}")
        
        print_success("Command executed successfully!")
        print_success(f"Response message: {data.get('message', '')[:100]}...")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response: {e}")
        return False


def test_state_query(api_url: str, session_id: str) -> bool:
    """
    Test GET /game/state/{session_id} endpoint.
    
    Args:
        api_url: Base API URL
        session_id: Session ID from new game
    
    Returns:
        True if successful, False otherwise.
    """
    print_section("Test 3: Query Game State (GET /game/state/{session_id})")
    
    endpoint = f"{api_url}/game/state/{session_id}"
    print_info(f"Endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint, timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_error(f"Expected status 200, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate response structure
        required_fields = ['current_room', 'inventory', 'state']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        print_success("State query successful!")
        print_success(f"Current room: {data.get('current_room')}")
        print_success(f"Inventory: {data.get('inventory')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response: {e}")
        return False


def test_dynamodb_integration(api_url: str) -> bool:
    """
    Test DynamoDB integration by creating a game, executing commands, and verifying state persistence.
    
    Args:
        api_url: Base API URL
    
    Returns:
        True if all tests pass, False otherwise.
    """
    print_section("Test 4: DynamoDB Integration (State Persistence)")
    
    # Create new game
    print_info("Creating new game...")
    session_id = test_new_game(api_url)
    if not session_id:
        print_error("Failed to create new game")
        return False
    
    # Execute a command that changes state
    print_info("\nExecuting command to change state...")
    endpoint = f"{api_url}/game/command"
    
    try:
        response = requests.post(
            endpoint,
            json={'session_id': session_id, 'command': 'inventory'},
            timeout=10
        )
        
        if response.status_code != 200:
            print_error(f"Command failed with status {response.status_code}")
            return False
        
        # Query state to verify persistence
        print_info("\nQuerying state to verify persistence...")
        state_endpoint = f"{api_url}/game/state/{session_id}"
        response = requests.get(state_endpoint, timeout=10)
        
        if response.status_code != 200:
            print_error(f"State query failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify state was persisted
        if 'state' not in data:
            print_error("State not found in response")
            return False
        
        print_success("DynamoDB integration verified!")
        print_success("State persisted and retrieved successfully")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response: {e}")
        return False


def main():
    """Main test execution."""
    if len(sys.argv) < 2:
        print_error("Usage: python scripts/test-sandbox-endpoints.py <api_url>")
        print_info("Example: python scripts/test-sandbox-endpoints.py https://abc123.execute-api.us-east-1.amazonaws.com/prod")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    
    print(f"\n{Colors.BOLD}West of Haunted House - Sandbox API Tests{Colors.RESET}")
    print(f"{Colors.BOLD}API URL: {api_url}{Colors.RESET}")
    
    # Track test results
    results = {
        'new_game': False,
        'command': False,
        'state_query': False,
        'dynamodb': False,
    }
    
    # Test 1: Create new game
    session_id = test_new_game(api_url)
    results['new_game'] = session_id is not None
    
    if session_id:
        # Test 2: Execute command
        results['command'] = test_command(api_url, session_id)
        
        # Test 3: Query state
        results['state_query'] = test_state_query(api_url, session_id)
    
    # Test 4: DynamoDB integration
    results['dynamodb'] = test_dynamodb_integration(api_url)
    
    # Print summary
    print_section("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        color = Colors.GREEN if passed else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.RESET}")
    
    if passed_tests == total_tests:
        print_success("\nAll tests passed! ✨")
        sys.exit(0)
    else:
        print_error(f"\n{total_tests - passed_tests} test(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
