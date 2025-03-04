#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import time


def run_command_with_retries(module, command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)

        if rc == 0:
            return stdout.strip(), None  # Success

        if attempt < retries - 1:
            module.warn(f"Retrying in {delay} seconds due to error: {stderr.strip()}")
            time.sleep(delay)  # Wait before retrying
        else:
            return None, f"Command failed after {retries} attempts: {stderr.strip()}"

    return None, "Unknown error"


def main():
    module_args = dict(
        expected_network_type=dict(type="str", required=True),  # Expected value (e.g., "OpenShiftSDN")
        max_retries=dict(type="int", default=3),  # Number of retries
        delay=dict(type="int", default=3),  # Delay between retries
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    command = ["oc", "get", "Network.config", "cluster", "-o", "json"]
    max_retries = module.params["max_retries"]
    delay = module.params["delay"]

    stdout, error = run_command_with_retries(module, command, retries=max_retries, delay=delay)

    if error:
        module.fail_json(msg=f"Failed to retrieve network config: {error}")

    try:
        network_config = json.loads(stdout)
        network_type = network_config.get("status", {}).get("migration", {}).get("networkType", "")

        if network_type == module.params["expected_network_type"]:
            module.exit_json(
                changed=False,
                msg=f"✅ Network migration type is correctly set to '{network_type}'.",
                network_type=network_type
            )
        else:
            module.fail_json(
                msg=f"❌ Network migration type is '{network_type}', expected '{module.params['expected_network_type']}'.",
                network_type=network_type
            )

    except json.JSONDecodeError:
        module.fail_json(msg="❌ Failed to parse network config JSON output.")


if __name__ == "__main__":
    main()
