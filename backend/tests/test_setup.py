# backend/tests/test_setup.py
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all core modules can be imported"""
    try:
        import config
        print("✓ Config imported successfully")
        
        from taxonomy_loader import taxonomy_loader
        print("✓ Taxonomy loader imported successfully")
        
        from sec_client import sec_client
        print("✓ SEC client imported successfully")
        
        # Test Arelle import
        from arelle import Cntlr
        print("✓ Arelle imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_taxonomy_path():
    """Test taxonomy file exists"""
    import config
    if config.US_GAAP_ENTRY_POINT.exists():
        print("✓ US-GAAP taxonomy file found")
        return True
    else:
        print(f"❌ Taxonomy file not found: {config.US_GAAP_ENTRY_POINT}")
        return False

if __name__ == "__main__":
    print("Testing XBRL Search App Setup...")
    print("=" * 40)
    
    test_imports()
    test_taxonomy_path()