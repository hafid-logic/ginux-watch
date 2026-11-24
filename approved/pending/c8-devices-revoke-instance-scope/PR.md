Adds one unit test (13 lines) to ginux-devices' existing test module; no production change.

revoke(instance) guards both teardown loops with an instance comparison, and neither guard had coverage: removing either still passed the whole suite, while revoke(1) would tear down another instance's descriptors and assignments.

revoke_only_tears_down_its_own_instance assigns and opens a device for two instances, revokes the first, and checks that the second instance's descriptor still resolves. It distinguishes a dead descriptor (InvalidDescriptor) from an alive-but-denied one (PermissionDenied on a zero device).

Evidence: baseline 96/96 pass across seven crates; each of the two mutants survives the existing suite and is killed by this test.

Prepared with AI assistance; reviewed by me.
