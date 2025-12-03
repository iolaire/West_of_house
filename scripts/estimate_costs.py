#!/usr/bin/env python3
"""
AWS Cost Estimation Script for West of Haunted House Backend

This script calculates estimated monthly AWS costs based on usage patterns
for Lambda (ARM64), DynamoDB (on-demand), and API Gateway.

Requirements: 21.5
"""

import json
from typing import Dict, Any


class AWSCostEstimator:
    """Estimates AWS costs for the game backend."""
    
    # Pricing data from AWS Pricing API (as of December 2025, us-east-1)
    LAMBDA_ARM_PRICING = {
        'requests': 0.0000002000,  # per request
        'compute_gb_second': 0.0000133334,  # per GB-second (Tier 1)
        'free_tier_requests': 1_000_000,  # per month
        'free_tier_compute': 400_000,  # GB-seconds per month
    }
    
    DYNAMODB_PRICING = {
        'read_request_unit': 0.0000001250,  # per read request unit
        'write_request_unit': 0.0000006250,  # per write request unit
        'storage_gb_month': 0.2500000000,  # per GB-month (beyond 25GB free tier)
        'free_tier_storage': 25,  # GB
    }
    
    API_GATEWAY_PRICING = {
        'requests': 0.0000035,  # per request (first 333M requests)
        'free_tier_requests': 1_000_000,  # per month (first 12 months)
    }
    
    def __init__(self, monthly_games: int = 1000):
        """
        Initialize cost estimator.
        
        Args:
            monthly_games: Expected number of games per month
        """
        self.monthly_games = monthly_games
        
    def estimate_lambda_costs(self) -> Dict[str, Any]:
        """
        Estimate Lambda costs for ARM64 architecture.
        
        Assumptions:
        - 128MB memory allocation
        - 500ms average execution time per request
        - ~15 requests per game (new game + 10 commands + 4 state queries)
        """
        memory_gb = 0.125  # 128MB = 0.125GB
        avg_duration_seconds = 0.5
        requests_per_game = 15
        
        total_requests = self.monthly_games * requests_per_game
        total_compute_gb_seconds = total_requests * memory_gb * avg_duration_seconds
        
        # Apply free tier
        billable_requests = max(0, total_requests - self.LAMBDA_ARM_PRICING['free_tier_requests'])
        billable_compute = max(0, total_compute_gb_seconds - self.LAMBDA_ARM_PRICING['free_tier_compute'])
        
        request_cost = billable_requests * self.LAMBDA_ARM_PRICING['requests']
        compute_cost = billable_compute * self.LAMBDA_ARM_PRICING['compute_gb_second']
        total_cost = request_cost + compute_cost
        
        return {
            'total_requests': total_requests,
            'total_compute_gb_seconds': round(total_compute_gb_seconds, 2),
            'billable_requests': billable_requests,
            'billable_compute_gb_seconds': round(billable_compute, 2),
            'request_cost': round(request_cost, 4),
            'compute_cost': round(compute_cost, 4),
            'total_cost': round(total_cost, 4),
            'free_tier_savings': round(
                (self.LAMBDA_ARM_PRICING['free_tier_requests'] * self.LAMBDA_ARM_PRICING['requests']) +
                (self.LAMBDA_ARM_PRICING['free_tier_compute'] * self.LAMBDA_ARM_PRICING['compute_gb_second']),
                4
            )
        }
    
    def estimate_dynamodb_costs(self) -> Dict[str, Any]:
        """
        Estimate DynamoDB costs for on-demand billing.
        
        Assumptions:
        - 1 write per new game (initial state)
        - 1 write per command (state update)
        - 1 read per command (load state)
        - 1 read per state query
        - Average session size: 5KB
        - Sessions expire after 1 hour (TTL cleanup)
        """
        writes_per_game = 11  # 1 new game + 10 commands
        reads_per_game = 14  # 10 commands + 4 state queries
        
        total_writes = self.monthly_games * writes_per_game
        total_reads = self.monthly_games * reads_per_game
        
        write_cost = total_writes * self.DYNAMODB_PRICING['write_request_unit']
        read_cost = total_reads * self.DYNAMODB_PRICING['read_request_unit']
        
        # Storage estimation
        avg_session_size_kb = 5
        avg_concurrent_sessions = 10  # Conservative estimate
        storage_gb = (avg_concurrent_sessions * avg_session_size_kb) / (1024 * 1024)
        billable_storage = max(0, storage_gb - self.DYNAMODB_PRICING['free_tier_storage'])
        storage_cost = billable_storage * self.DYNAMODB_PRICING['storage_gb_month']
        
        total_cost = write_cost + read_cost + storage_cost
        
        return {
            'total_writes': total_writes,
            'total_reads': total_reads,
            'write_cost': round(write_cost, 4),
            'read_cost': round(read_cost, 4),
            'storage_gb': round(storage_gb, 6),
            'billable_storage_gb': round(billable_storage, 6),
            'storage_cost': round(storage_cost, 4),
            'total_cost': round(total_cost, 4),
            'free_tier_storage': self.DYNAMODB_PRICING['free_tier_storage']
        }
    
    def estimate_api_gateway_costs(self) -> Dict[str, Any]:
        """
        Estimate API Gateway costs.
        
        Assumptions:
        - All Lambda invocations go through API Gateway
        - ~15 API requests per game
        """
        requests_per_game = 15
        total_requests = self.monthly_games * requests_per_game
        
        # Apply free tier (first 12 months only)
        billable_requests = max(0, total_requests - self.API_GATEWAY_PRICING['free_tier_requests'])
        total_cost = billable_requests * self.API_GATEWAY_PRICING['requests']
        
        return {
            'total_requests': total_requests,
            'billable_requests': billable_requests,
            'total_cost': round(total_cost, 4),
            'free_tier_savings': round(
                self.API_GATEWAY_PRICING['free_tier_requests'] * self.API_GATEWAY_PRICING['requests'],
                4
            )
        }
    
    def estimate_amplify_hosting_costs(self) -> Dict[str, Any]:
        """
        Estimate Amplify Hosting costs.
        
        Assumptions:
        - React frontend hosted on Amplify
        - ~5MB per page load
        - 1 page load per game
        - Free tier: 15GB served/month
        """
        mb_per_game = 5
        total_mb = self.monthly_games * mb_per_game
        total_gb = total_mb / 1024
        
        free_tier_gb = 15
        billable_gb = max(0, total_gb - free_tier_gb)
        
        cost_per_gb = 0.15
        total_cost = billable_gb * cost_per_gb
        
        return {
            'total_gb_served': round(total_gb, 2),
            'billable_gb': round(billable_gb, 2),
            'total_cost': round(total_cost, 4),
            'free_tier_gb': free_tier_gb
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost estimation report."""
        lambda_costs = self.estimate_lambda_costs()
        dynamodb_costs = self.estimate_dynamodb_costs()
        api_gateway_costs = self.estimate_api_gateway_costs()
        amplify_costs = self.estimate_amplify_hosting_costs()
        
        total_monthly_cost = (
            lambda_costs['total_cost'] +
            dynamodb_costs['total_cost'] +
            api_gateway_costs['total_cost'] +
            amplify_costs['total_cost']
        )
        
        return {
            'assumptions': {
                'monthly_games': self.monthly_games,
                'requests_per_game': 15,
                'avg_lambda_duration_ms': 500,
                'lambda_memory_mb': 128,
                'lambda_architecture': 'ARM64',
                'dynamodb_billing': 'on-demand',
                'session_ttl_hours': 1,
            },
            'lambda': lambda_costs,
            'dynamodb': dynamodb_costs,
            'api_gateway': api_gateway_costs,
            'amplify_hosting': amplify_costs,
            'total_monthly_cost': round(total_monthly_cost, 2),
            'target_monthly_cost': 5.00,
            'under_target': total_monthly_cost < 5.00,
            'cost_breakdown_percentage': {
                'lambda': round((lambda_costs['total_cost'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 1),
                'dynamodb': round((dynamodb_costs['total_cost'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 1),
                'api_gateway': round((api_gateway_costs['total_cost'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 1),
                'amplify_hosting': round((amplify_costs['total_cost'] / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 1),
            }
        }
    
    def print_report(self):
        """Print formatted cost estimation report."""
        report = self.generate_report()
        
        print("=" * 80)
        print("AWS COST ESTIMATION REPORT")
        print("West of Haunted House Backend")
        print("=" * 80)
        print()
        
        print("ASSUMPTIONS:")
        print(f"  Monthly Games: {report['assumptions']['monthly_games']:,}")
        print(f"  Requests per Game: {report['assumptions']['requests_per_game']}")
        print(f"  Lambda Memory: {report['assumptions']['lambda_memory_mb']}MB ({report['assumptions']['lambda_architecture']})")
        print(f"  Lambda Duration: {report['assumptions']['avg_lambda_duration_ms']}ms average")
        print(f"  DynamoDB Billing: {report['assumptions']['dynamodb_billing']}")
        print(f"  Session TTL: {report['assumptions']['session_ttl_hours']} hour")
        print()
        
        print("-" * 80)
        print("LAMBDA (ARM64)")
        print("-" * 80)
        print(f"  Total Requests: {report['lambda']['total_requests']:,}")
        print(f"  Total Compute: {report['lambda']['total_compute_gb_seconds']:,} GB-seconds")
        print(f"  Billable Requests: {report['lambda']['billable_requests']:,}")
        print(f"  Billable Compute: {report['lambda']['billable_compute_gb_seconds']:,} GB-seconds")
        print(f"  Request Cost: ${report['lambda']['request_cost']:.4f}")
        print(f"  Compute Cost: ${report['lambda']['compute_cost']:.4f}")
        print(f"  Free Tier Savings: ${report['lambda']['free_tier_savings']:.4f}")
        print(f"  TOTAL: ${report['lambda']['total_cost']:.2f}")
        print()
        
        print("-" * 80)
        print("DYNAMODB (ON-DEMAND)")
        print("-" * 80)
        print(f"  Total Writes: {report['dynamodb']['total_writes']:,}")
        print(f"  Total Reads: {report['dynamodb']['total_reads']:,}")
        print(f"  Write Cost: ${report['dynamodb']['write_cost']:.4f}")
        print(f"  Read Cost: ${report['dynamodb']['read_cost']:.4f}")
        print(f"  Storage: {report['dynamodb']['storage_gb']:.6f} GB")
        print(f"  Billable Storage: {report['dynamodb']['billable_storage_gb']:.6f} GB")
        print(f"  Storage Cost: ${report['dynamodb']['storage_cost']:.4f}")
        print(f"  Free Tier: {report['dynamodb']['free_tier_storage']} GB storage")
        print(f"  TOTAL: ${report['dynamodb']['total_cost']:.2f}")
        print()
        
        print("-" * 80)
        print("API GATEWAY")
        print("-" * 80)
        print(f"  Total Requests: {report['api_gateway']['total_requests']:,}")
        print(f"  Billable Requests: {report['api_gateway']['billable_requests']:,}")
        print(f"  Free Tier Savings: ${report['api_gateway']['free_tier_savings']:.4f}")
        print(f"  TOTAL: ${report['api_gateway']['total_cost']:.2f}")
        print()
        
        print("-" * 80)
        print("AMPLIFY HOSTING")
        print("-" * 80)
        print(f"  Total Data Served: {report['amplify_hosting']['total_gb_served']:.2f} GB")
        print(f"  Billable Data: {report['amplify_hosting']['billable_gb']:.2f} GB")
        print(f"  Free Tier: {report['amplify_hosting']['free_tier_gb']} GB")
        print(f"  TOTAL: ${report['amplify_hosting']['total_cost']:.2f}")
        print()
        
        print("=" * 80)
        print("MONTHLY COST SUMMARY")
        print("=" * 80)
        print(f"  Lambda (ARM64): ${report['lambda']['total_cost']:.2f} ({report['cost_breakdown_percentage']['lambda']}%)")
        print(f"  DynamoDB: ${report['dynamodb']['total_cost']:.2f} ({report['cost_breakdown_percentage']['dynamodb']}%)")
        print(f"  API Gateway: ${report['api_gateway']['total_cost']:.2f} ({report['cost_breakdown_percentage']['api_gateway']}%)")
        print(f"  Amplify Hosting: ${report['amplify_hosting']['total_cost']:.2f} ({report['cost_breakdown_percentage']['amplify_hosting']}%)")
        print()
        print(f"  TOTAL MONTHLY COST: ${report['total_monthly_cost']:.2f}")
        print(f"  TARGET COST: ${report['target_monthly_cost']:.2f}")
        print()
        
        if report['under_target']:
            savings = report['target_monthly_cost'] - report['total_monthly_cost']
            print(f"  ✅ UNDER TARGET by ${savings:.2f} ({(savings/report['target_monthly_cost']*100):.1f}%)")
        else:
            overage = report['total_monthly_cost'] - report['target_monthly_cost']
            print(f"  ⚠️  OVER TARGET by ${overage:.2f} ({(overage/report['target_monthly_cost']*100):.1f}%)")
        
        print("=" * 80)
        print()


def main():
    """Run cost estimation for different usage scenarios."""
    scenarios = [
        (1000, "Target Usage (1,000 games/month)"),
        (500, "Low Usage (500 games/month)"),
        (2000, "High Usage (2,000 games/month)"),
        (5000, "Very High Usage (5,000 games/month)"),
    ]
    
    for monthly_games, description in scenarios:
        print(f"\n{'=' * 80}")
        print(f"SCENARIO: {description}")
        print(f"{'=' * 80}\n")
        
        estimator = AWSCostEstimator(monthly_games=monthly_games)
        estimator.print_report()
        
        # Save JSON report to documents/cost-analysis/
        report = estimator.generate_report()
        
        # Create output directory if it doesn't exist
        import os
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'documents', 'cost-analysis')
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"cost_estimate_{monthly_games}_games.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Detailed report saved to: {filepath}\n")


if __name__ == "__main__":
    main()
