from ansible.module_utils.basic import AnsibleModule
import time
import json


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def patch_network_operator(module, timeout, network_provider_config):
    """Patch the Network operator configuration."""
    """Patch the Network operator configuration safely using json.dumps."""

    patch_data = {
        "spec": {
            "defaultNetwork": {
                network_provider_config: None  # Setting config to `null`
            }
        }
    }

    command = [
        "oc", "patch", "Network.operator.openshift.io", "cluster",
        "--type=merge", "--patch", json.dumps(patch_data)
    ]

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(module, command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)
            if not error:
                return output
        except Exception as ex:
            module.fail_json(msg=str(ex))


def delete_namespace(module, timeout, namespace):
    """Delete a specified namespace."""
    command = f"oc delete namespace {namespace}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(module, command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)
            if not error:
                return output
        except Exception as ex:
            module.fail_json(msg=str(ex))


def main():
    module = AnsibleModule(
        argument_spec={
            "network_provider_config": {"type": "str", "required": True},
            "namespace": {"type": "str", "required": False},
            "timeout": {"type": "int", "default": 120},  # Timeout in seconds
        },
        supports_check_mode=True,
    )

    network_provider_config = module.params["network_provider_config"]
    namespace = module.params.get("namespace")
    timeout = module.params["timeout"]

    try:
        # Apply the patches to the Network operator configuration
        patch_network_operator(module, timeout, network_provider_config)

        # Delete the namespace if provided
        if namespace:
            delete_namespace(module, timeout, namespace)

        module.exit_json(
            changed=True,
            msg="Network configuration updated and namespace deleted if provided.",
        )

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
