def robot_demo(start_sample_number, end_sample_number, robot):
    while True:
        for sample_number in range(start_sample_number, end_sample_number):
            set_and_wait(robot.sample_number, sample_number)
            set_and_wait(robot.load_cmd, 1)
            set_and_wait(robot.execute_cmd.put(1))

            while robot.status.get() != 'Idle':
                time.sleep(.1)

