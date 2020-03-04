class RemoteDebugger:
    def setup_remote_pydev_debug(host, port):
        error_msg = ('Error setting up the debug environment. Verify that the'
                     ' option pydev_worker_debug_host is pointing to a valid '
                     'hostname or IP on which a pydev server is listening on'
                     ' the port indicated by pydev_worker_debug_port.')
        try:
            try:
                from pydev import pydevd
            except ImportError:
                import pydevd

            pydevd.settrace(host,
                            port=port,
                            stdoutToServer=True,
                            stderrToServer=True)
            return True
        except Exception:
            print(error_msg)