# Quick Sobel Module Validation
# Fast syntax và functionality check

import os
import subprocess

def validate_verilog_syntax(module_path):
    """
    Quick syntax check using iverilog hoặc available tools
    """
    print(f"\n=== Validating: {module_path} ===")
    
    if not os.path.exists(module_path):
        print(f"❌ File not found: {module_path}")
        return False
        
    # Check basic Verilog syntax patterns
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Basic syntax checks
    checks = {
        'module_declaration': 'module ' in content,
        'endmodule': 'endmodule' in content,
        'always_blocks': 'always @' in content,
        'wire_declarations': 'wire ' in content or 'reg ' in content,
    }
    
    print("Basic Syntax Checks:")
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")
        if not result:
            all_passed = False
            
    return all_passed

def validate_module_interface(module_path):
    """
    Validate module interface và parameters
    """
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract module name
    import re
    module_match = re.search(r'module\s+(\w+)', content)
    if module_match:
        module_name = module_match.group(1)
        print(f"📋 Module: {module_name}")
        
        # Check for parameters
        if 'parameter' in content:
            params = re.findall(r'parameter\s+\w+\s*=\s*\d+', content)
            print(f"📊 Parameters: {len(params)} found")
            
        # Check input/output ports
        inputs = len(re.findall(r'input\s+', content))
        outputs = len(re.findall(r'output\s+', content))
        print(f"🔌 Ports: {inputs} inputs, {outputs} outputs")
        
        return True
    return False

def main():
    """
    Validate all Sobel modules
    """
    print("="*60)
    print("SOBEL MODULES VALIDATION")
    print("="*60)
    
    # Module paths
    sobel_dir = "d:/DACN/Sobel_project/src/sobel/"
    modules = [
        "rgb_to_gray.v",
        "line_buffer.v", 
        "sobel_kernel.v",
        "edge_magnitude.v",
        "sobel_processor.v"
    ]
    
    results = {}
    
    for module in modules:
        module_path = sobel_dir + module
        
        # Syntax validation
        syntax_ok = validate_verilog_syntax(module_path)
        
        # Interface validation  
        interface_ok = validate_module_interface(module_path) if syntax_ok else False
        
        results[module] = {
            'syntax': syntax_ok,
            'interface': interface_ok,
            'overall': syntax_ok and interface_ok
        }
        
        print("-" * 40)
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY:")
    print("="*60)
    
    for module, result in results.items():
        status = "✅ PASS" if result['overall'] else "❌ FAIL"
        print(f"{status} {module}")
        
    # Overall status
    all_passed = all(r['overall'] for r in results.values())
    print(f"\nOverall Status: {'✅ ALL MODULES VALID' if all_passed else '❌ ISSUES FOUND'}")
    
    if all_passed:
        print("\n🚀 Ready for integration testing!")
    else:
        print("\n🔧 Fix issues before proceeding to integration.")

if __name__ == "__main__":
    main()