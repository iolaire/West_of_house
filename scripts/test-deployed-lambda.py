#!/usr/bin/env python3
"""
Test script for deployed Lambda function (direct invocation).

This script tests the Lambda function directly without API Gateway:
1. Create new game session
2. Execute game commands
3. Query game state
4. Verify DynamoDB session storage

Requirements: 11.1, 11.2, 21.1

Usage:
    python scripts/test-deployed-lambda.py <function_name>

Example:
    python scripts/test-deployed-lambda.py amplify-westofhouse-iolaire-sa-gamehandler9C35C05F-7OssIrbwmAhb
"""

import sys
import json
import boto3
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


def invoke_lambda(lambda_client, function_name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Invoke Lambda function with payload.
    
    Args:
        lambda_client: Boto3 Lambda client
        function_name: Lambda function name
        payload: Request payload
    
    Returns:
        Response data if successful, None otherwise.
    """
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Read response payload
        response_payload = json.loads(response['Payload'].read())
        
        # Check for Lambda errors
        if 'FunctionError' in response:
            print_error(f"Lambda function error: {response.get('FunctionError')}")
            print_error(f"Response: {json.dumps(response_payload, indent=2)}")
            return None
        
        return response_payload
        
    except Exception as e:
        print_error(f"Failed to invoke Lambda: {e}")
        return None


def test_new_game(lambda_client, function_name: str) -> Optional[str]:
    """
    Test new game creation.
    
    Returns:
        Session ID if successful, None otherwise.
    """
    print_section("Test 1: Create New Game")
    
    print_info(f"Function: {function_name}")
    print_info("Action: new_game")
    
    # Create API Gateway-like event
    payload = {
        'httpMethod': 'POST',
        'path': '/game/new',
        'body': json.dumps({})
    }
    
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = invoke_lambda(lambda_client, function_name, payload)
    
    if not response:
        print_error("Failed to invoke Lambda")
        return None
    
    print_info(f"Response: {json.dumps(response, indent=2)}")
    
    # Parse response body
    if 'body' in response:
        try:
            body = json.loads(response['body'])
        except json.JSONDecodeError:
            body = response
    else:
        body = response
    
    # Check status code
    status_code = response.get('statusCode', 200)
    if status_code != 200:
        print_error(f"Expected status 200, got {status_code}")
        return None
    
    # Validate response structure
    required_fields = ['session_id', 'room', 'description', 'state']
    missing_fields = [field for field in required_fields if field not in body]
    
    if missing_fields:
        print_error(f"Missing required fields: {missing_fields}")
        return None
    
    # Validate state structure
    state = body.get('state', {})
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
    
    session_id = body.get('session_id')
    print_success(f"New game created successfully!")
    print_success(f"Session ID: {session_id}")
    print_success(f"Starting room: {body.get('room')}")
    
    return session_id


def test_command(lambda_client, function_name: str, session_id: str, command: str) -> bool:
    """
    Test command execution.
    
    Args:
        lambda_client: Boto3 Lambda client
        function_name: Lambda function name
        session_id: Session ID from new game
        command: Command to execute
    
    Returns:
        True if successful, False otherwise.
    """
    print_section(f"Test 2: Execute Command - '{command}'")
    
    print_info(f"Function: {function_name}")
    print_info(f"Session ID: {session_id}")
    print_info(f"Command: {command}")
    
    # Create API Gateway-like event
    payload = {
        'httpMethod': 'POST',
        'path': '/game/command',
        'body': json.dumps({
            'session_id': session_id,
            'command': command
        })
    }
    
    response = invoke_lambda(lambda_client, function_name, payload)
    
    if not response:
        print_error("Failed to invoke Lambda")
        return False
    
    print_info(f"Response: {json.dumps(response, indent=2)}")
    
    # Parse response body
    if 'body' in response:
        try:
            body = json.loads(response['body'])
        except json.JSONDecodeError:
            body = response
    else:
        body = response
    
    # Check status code
    status_code = response.get('statusCode', 200)
    if status_code != 200:
        print_error(f"Expected status 200, got {status_code}")
        return False
    
    # Validate response structure
    required_fields = ['success', 'message']
    missing_fields = [field for field in required_fields if field not in body]
    
    if missing_fields:
        print_error(f"Missing required fields: {missing_fields}")
        return False
    
    if not body.get('success'):
        print_warning(f"Command execution reported failure: {body.get('message')}")
    
    print_success("Command executed successfully!")
    message = body.get('message', '')
    if len(message) > 100:
        print_success(f"Response message: {message[:100]}...")
    else:
        print_success(f"Response message: {message}")
    
    return True


def test_state_query(lambda_client, function_name: str, session_id: str) -> bool:
    """
    Test state query.
    
    Args:
        lambda_client: Boto3 Lambda client
        function_name: Lambda function name
        session_id: Session ID from new game
    
    Returns:
        True if successful, False otherwise.
    """
    print_section("Test 3: Query Game State")
    
    print_info(f"Function: {function_name}")
    print_info(f"Session ID: {session_id}")
    
    # Create API Gateway-like event
    payload = {
        'httpMethod': 'GET',
        'path': f'/game/state/{session_id}',
        'pathParameters': {
            'session_id': session_id
        }
    }
    
    response = invoke_lambda(lambda_client, function_name, payload)
    
    if not response:
        print_error("Failed to invoke Lambda")
        return False
    
    print_info(f"Response: {json.dumps(response, indent=2)}")
    
    # Parse response body
    if 'body' in response:
        try:
            body = json.loads(response['body'])
        except json.JSONDecodeError:
            body = response
    else:
        body = response
    
    # Check status code
    status_code = response.get('statusCode', 200)
    if status_code != 200:
        print_error(f"Expected status 200, got {status_code}")
        return False
    
    # Validate response structure
    required_fields = ['current_room', 'inventory', 'state']
    missing_fields = [field for field in required_fields if field not in body]
    
    if missing_fields:
        print_error(f"Missing required fields: {missing_fields}")
        return False
    
    print_success("State query successful!")
    print_success(f"Current room: {body.get('current_room')}")
    print_success(f"Inventory: {body.get('inventory')}")
    
    return True


def test_dynamodb_storage(dynamodb_client, session_id: str) -> bool:
    """
    Test DynamoDB session storage.
    
    Args:
        dynamodb_client: Boto3 DynamoDB client
        session_id: Session ID to verify
    
    Returns:
        True if session exists in DynamoDB, False otherwise.
    """
    print_section("Test 4: Verify DynamoDB Session Storage")
    
    table_name = "WestOfHauntedHouse-GameSessions"
    print_info(f"Table: {table_name}")
    print_info(f"Session ID: {session_id}")
    
    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={'sessionId': {'S': session_id}}
        )
        
        if 'Item' not in response:
            print_error("Session not found in DynamoDB")
            return False
        
        item = response['Item']
        print_info(f"DynamoDB Item: {json.dumps(item, indent=2, default=str)}")
        
        # Validate item structure
        required_fields = ['sessionId', 'currentRoom', 'inventory', 'state']
        missing_fields = [field for field in required_fields if field not in item]
        
        if missing_fields:
            print_warning(f"Missing fields in DynamoDB item: {missing_fields}")
        
        print_success("Session found in DynamoDB!")
        print_success(f"Current room: {item.get('currentRoom', {}).get('S', 'N/A')}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to query DynamoDB: {e}")
        return False


def main():
    """Main test execution."""
    if len(sys.argv) < 2:
        print_error("Usage: python scripts/test-deployed-lambda.py <function_name>")
        print_info("Example: python scripts/test-deployed-lambda.py amplify-westofhouse-iolaire-sa-gamehandler9C35C05F-7OssIrbwmAhb")
        sys.exit(1)
    
    function_name = sys.argv[1]
    
    print(f"\n{Colors.BOLD}West of Haunted House - Lambda Function Tests{Colors.RESET}")
    print(f"{Colors.BOLD}Function: {function_name}{Colors.RESET}")
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda')
    dynamodb_client = boto3.client('dynamodb')
    
    # Track test results
    results = {
        'new_game': False,
        'command_look': False,
        'command_inventory': False,
        'command_go_north': False,
        'state_query': False,
        'dynamodb_storage': False,
    }
    
    # Test 1: Create new game
    session_id = test_new_game(lambda_client, function_name)
    results['new_game'] = session_id is not None
    
    if session_id:
        # Test 2: Execute commands
        results['command_look'] = test_command(lambda_client, function_name, session_id, 'look')
        results['command_inventory'] = test_command(lambda_client, function_name, session_id, 'inventory')
        results['command_go_north'] = test_command(lambda_client, function_name, session_id, 'go north')
        
        # Test 3: Query state
        results['state_query'] = test_state_query(lambda_client, function_name, session_id)
        
        # Test 4: Verify DynamoDB storage
        results['dynamodb_storage'] = test_dynamodb_storage(dynamodb_client, session_id)
    
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
