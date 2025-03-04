#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import time


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def wait_for_network_co(module, timeout):
    """Wait until the Network CO enters the PROGRESSING=True condition."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        command = "oc wait co network --for='condition=PROGRESSING=True' --timeout=60s"
        _, error = run_command(module, command)
        if not error:
            return "Network Cluster Operator is in PROGRESSING=True state."
        time.sleep(10)  # Retry every 10 seconds
    return "Timeout waiting for Network Cluster Operator to reach PROGRESSING=True."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(type="int", required=True),
        )
    )

    timeout = module.params["timeout"]

    result_message = wait_for_network_co(module, timeout)
    if "Timeout" in result_message:
        module.fail_json(msg=result_message)
    else:
        module.exit_json(changed=False, msg=result_message)


if __name__ == "__main__":
    main()
