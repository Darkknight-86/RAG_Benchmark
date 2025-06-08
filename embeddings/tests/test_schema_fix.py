#!/usr/bin/env python3
"""
Test script to check and fix the ClickHouse table schema.
"""

from src.rag.Adapters.ClickHouseAdapter import ClickHouseAdapter

def main():
    print("Initializing ClickHouse adapter...")
    try:
        adapter = ClickHouseAdapter()
        print("✅ ClickHouse adapter initialized successfully")

        # Check current schema
        print("\n=== Checking Current Table Schema ===")
        existing_cols, missing_cols, extra_cols = adapter.check_table_schema()

        if missing_cols or extra_cols:
            print(f"\n⚠️  Schema mismatch detected!")
            print("Would you like to recreate the table? (yes/no):")
            response = input().strip().lower()

            if response == 'yes':
                success = adapter.recreate_table()
                if success:
                    print("✅ Table recreation completed successfully")
                else:
                    print("❌ Table recreation failed")
            else:
                print("Schema recreation skipped")
        else:
            print("✅ Schema is already correct!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()