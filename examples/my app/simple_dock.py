# simple_dock
#
# Le niveau de batterie faible par défaut pour Cozmo est de 3.65. (ligne 104 et 127)
# import required functions

import sys, os, datetime, random, time, math, re, threading, asyncio, cozmo, cozmo.objects, cozmo.util
from cozmo.util import Angle, degrees, distance_mm, speed_mmps
from cozmo.objects import CustomObjectMarkers, CustomObjectTypes, LightCube
from cozmo.robot_alignment import RobotAlignmentTypes
from cozmo import connect_on_loop

global freeplay
global robot

freeplay = 0
stop = True
robot = cozmo.robot.Robot

# CUBE USAGE
#
# value of 0: cube's wifi off & cube's lights off
# value of 1: cube's wifi on & enables all games
# value of 2: cube's wifi on & cube's lights on during freeplay
# value between 0 and 2
use_cubes = 2

# main program and loops

def cozmo_unleashed(robot: cozmo.robot.Robot):
    global freeplay

    robot.world.charger = None
    charger = None

    robot.clear_idle_animation()
    robot.stop_all_motors()
    robot.abort_all_actions(False)
    robot.wait_for_all_actions_completed()
    time.sleep(1)

    robot.world.auto_disconnect_from_cubes_at_end(enable=True)
    robot.enable_all_reaction_triggers(False)
    robot.enable_stop_on_cliff(True)
    robot.set_robot_volume(0.04)

    if use_cubes == 2:
        robot.enable_freeplay_cube_lights(enable=True)
    time.sleep(3)

# State 1: on charger, charging
    if (robot.is_on_charger == 1) and (robot.is_charging == 1):
        ##
        print("State: charging, battery %s" %
                str(round(robot.battery_voltage, 2)))
        i = random.randint(1, 100)
        ##
        if i >= 97:
            robot.play_anim(
                "anim_guarddog_fakeout_02").wait_for_completed()
            robot.wait_for_all_actions_completed()
        elif i >= 85:
            robot.play_anim(
                "anim_gotosleep_sleeploop_01").wait_for_completed()
            robot.wait_for_all_actions_completed()
        ##
        time.sleep(2)
        robot.set_all_backpack_lights(cozmo.lights.green_light)
        ##
        time.sleep(2)
        robot.set_all_backpack_lights(cozmo.lights.off_light)

# State 2: on charger, fully charged
    if (robot.is_on_charger == 1) and (robot.is_charging == 0):
        if freeplay == 0:
            print("State: charged, battery %s" %
                    str(round(robot.battery_voltage, 2)))
            ##
            robot.set_needs_levels(1, 1, 1)
            robot.clear_idle_animation()
            robot.set_all_backpack_lights(cozmo.lights.off_light)
            robot.play_anim(
                "anim_launch_altwakeup_01").wait_for_completed()
            robot.wait_for_all_actions_completed()
            time.sleep(2)
            ##
            robot.drive_off_charger_contacts(
                num_retries=3, in_parallel=False).wait_for_completed()
            robot.move_lift(-3)
            ##
            try:
                if (robot.is_on_charger == 1):
                    robot.drive_straight(distance_mm(80), speed_mmps(
                        25), num_retries=1).wait_for_completed()
            finally:
                pass
                ##
            robot.wait_for_all_actions_completed()
            time.sleep(2)

# State 3: not on charger, good battery | default low battery is 3.65
    if (robot.battery_voltage > 3.7) and (robot.is_on_charger == 0):
        print("State: good battery playtime, battery %s" %
                str(round(robot.battery_voltage, 2)))
        time.sleep(3)

# State 4: not on charger, low battery | default low battery is 3.65
    if (robot.battery_voltage <= 5) and (robot.is_on_charger == 0):
        print("State: finding charger, battery %s" %
                str(round(robot.battery_voltage, 2)))
        ##
        robot.enable_all_reaction_triggers(True)
        ##
        # recherche de l'emplacement du chargeur
        # voir si nous savons déjà où se trouve le chargeur
        if charger != None:
            # nous savons où se trouve le chargeur
            robot.move_lift(-3)

            print("State: start of loop, charger position known, battery %s" % str(
                round(robot.battery_voltage, 2)))
            ##
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSurprise,
                                    ignore_body_track=True, ignore_head_track=True).wait_for_completed()
            robot.set_head_angle(degrees(0)).wait_for_completed()
            robot.wait_for_all_actions_completed()
            time.sleep(0.01)
            ##
            print(str(charger))
            ##
            if charger != None:
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        110), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        80), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                    80), angle_tolerance=None, is_absolute=True).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(1)
                ##
        else:
            # nous savons où se trouve le chargeur mais nous avons été délocalisés.
            print("State: did not find charger after clearing map, battery %s" % str(
                round(robot.battery_voltage, 2)))
            ##
        # nous ne savons pas où se trouve le chargeur
        if not charger:
            # nous allons chercher le chargeur sur place pendant 30 secondes
            robot.enable_all_reaction_triggers(True)

            print("State: look around for charger, battery %s" %
                    str(round(robot.battery_voltage, 2)))
            robot.play_anim_trigger(
                cozmo.anim.Triggers.SparkIdle, ignore_body_track=True).wait_for_completed()
            time.sleep(0.5)
            robot.set_head_angle(degrees(0)).wait_for_completed()
            robot.move_lift(-3)
            time.sleep(1)
            robot.start_behavior(
                cozmo.behavior.BehaviorTypes.LookAroundInPlace)
            try:
                charger = robot.world.wait_for_observed_charger(
                    timeout=45, include_existing=True)

                print("State: found charger in lookaround!, battery %s" %
                        str(round(robot.battery_voltage, 2)))
            except asyncio.TimeoutError:
                robot.start_behavior(
                    cozmo.behavior.BehaviorTypes.LookAroundInPlace).stop()

                print("State: unable to find charger in lookaround, battery %s" % str(
                    round(robot.battery_voltage, 2)))
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabUnhappy, in_parallel=True,
                                        ignore_body_track=True, ignore_head_track=True).wait_for_completed()
                robot.set_head_angle(
                    degrees(0), in_parallel=True).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(2)
            finally:
                # arrêter le comportement de lookaround
                robot.start_behavior(
                    cozmo.behavior.BehaviorTypes.LookAroundInPlace).stop()

                print("State: stop lookaround routine, battery %s" %
                        str(round(robot.battery_voltage, 2)))
            robot.clear_idle_animation()
            robot.wait_for_all_actions_completed()
            time.sleep(2)
            ##
        # Emplacement du chargeur et manipulation de l'amarrage ici
        if charger:
            while (robot.is_on_charger == 0):
                # Oui ! Essayez de conduire à proximité du chargeur, puis arrêtez-vous.

                print("State: moving to charger, battery %s" %
                        str(round(robot.battery_voltage, 2)))
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabChatty, ignore_lift_track=True,
                                        ignore_body_track=True, ignore_head_track=True).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(1)
                robot.move_lift(-3)
                robot.set_head_angle(degrees(0)).wait_for_completed()
                ##
                # Si vous utilisez Cozmo sur un tapis, essayez de faire passer le nombre de répétitions à 4 ou 5.
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        160), RobotAlignmentTypes.LiftPlate, num_retries=2)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        120), RobotAlignmentTypes.LiftPlate, num_retries=2)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        100), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        80), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        60), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                time.sleep(2)
                try:
                    robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                        80), angle_tolerance=None, is_absolute=True, num_retries=2).wait_for_completed()
                finally:
                    pass
                try:
                    robot.drive_straight(
                        distance_mm(-70), speed_mmps(50), num_retries=1).wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        90), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        60), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                try:
                    action = robot.go_to_object(charger, distance_mm(
                        40), RobotAlignmentTypes.LiftPlate, num_retries=3)
                    action.wait_for_completed()
                finally:
                    pass
                time.sleep(1)
                ##
                # on devrait être juste en face du chargeur, on le voit ?
                if (charger.is_visible == False):
                    # nous savons où se trouve le chargeur
                    try:
                        if robot.is_picked_up == True:
                            robot.stop_all_motors()
                            robot.abort_all_actions(False)
                            robot.clear_idle_animation()
                            robot.wait_for_all_actions_completed()
                            time.sleep(1)
                            charger = None
                            robot.world.charger = None

                            print("State: robot picked up during docking, resetting, battery %s" % str(
                                round(robot.battery_voltage, 2)))
                            break
                    finally:
                        pass

                    print("State: can't see charger, position is still known, battery %s" % str(
                        round(robot.battery_voltage, 2)))
                    robot.play_anim_trigger(
                        cozmo.anim.Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
                    robot.set_head_angle(degrees(0)).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1)

                    print(charger)
                    try:
                        action = robot.go_to_object(charger, distance_mm(
                            110), RobotAlignmentTypes.LiftPlate, num_retries=3)
                        action.wait_for_completed()
                    finally:
                        pass
                    try:
                        action = robot.go_to_object(charger, distance_mm(
                            80), RobotAlignmentTypes.LiftPlate, num_retries=3)
                        action.wait_for_completed()
                    finally:
                        pass
                    robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                        80), angle_tolerance=None, is_absolute=True).wait_for_completed()
                    robot.drive_straight(
                        distance_mm(-50), speed_mmps(50)).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1)
                    if (charger.is_visible == False):
                        # on ne sait plus où est le chargeur.
                        robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeReaction, ignore_body_track=True,
                                                ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
                        time.sleep(0.5)
                        robot.drive_straight(
                            distance_mm(-70), speed_mmps(50)).wait_for_completed()
                        robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                            80), angle_tolerance=None, is_absolute=True).wait_for_completed()
                        robot.wait_for_all_actions_completed()

                        print("State: charger not found, clearing map. battery %s" % str(
                            round(robot.battery_voltage, 2)))
                        time.sleep(1)
                        robot.world.charger = None
                        charger = None
                        break
                    else:
                        break
                i = random.randint(1, 100)
                if i >= 85:
                    robot.play_anim_trigger(cozmo.anim.Triggers.FeedingReactToShake_Normal,
                                            ignore_body_track=True, ignore_head_track=True).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1)
                # Dock. Faites demi-tour et conduisez en arrière

                print("State: docking, battery %s" %
                        str(round(robot.battery_voltage, 2)))
                robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees - 180), accel=degrees(
                    80), angle_tolerance=None, is_absolute=True).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(0.1)
                robot.play_anim_trigger(cozmo.anim.Triggers.CubePounceFake, ignore_body_track=True,
                                        ignore_lift_track=True, ignore_head_track=True).wait_for_completed()
                robot.set_head_angle(degrees(0)).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(0.1)
                robot.enable_all_reaction_triggers(True)
                backup_count = 0
                while robot.is_on_charger == 0:
                    try:
                        robot.backup_onto_charger(max_drive_time=2)
                    except robot.is_on_charger == 1:
                        robot.stop_all_motors()
                        print("State: Contact! Stop all motors, battery %s" % str(
                            round(robot.battery_voltage, 2)))
                    robot.wait_for_all_actions_completed()
                    backup_count += 1
                    time.sleep(1)
                    if robot.is_on_charger == 1:
                        print("State: Robot is on Charger, battery %s" %
                                str(round(robot.battery_voltage, 2)))
                        robot.enable_all_reaction_triggers(False)
                        break
                    elif backup_count == 6:
                        robot.enable_all_reaction_triggers(False)
                        break
                robot.wait_for_all_actions_completed()
                time.sleep(0.1)
                ##
                # vérifier si nous sommes maintenant à quai
                if robot.is_on_charger:
                    # Oui ! On est à quai !
                    robot.play_anim(
                        "anim_sparking_success_02").wait_for_completed()
                    robot.set_head_angle(degrees(0)).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1.5)

                    print("State: I am now docked, battery %s" %
                            str(round(robot.battery_voltage, 2)))
                    robot.set_all_backpack_lights(cozmo.lights.off_light)
                    robot.play_anim(
                        "anim_gotosleep_getin_01").wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1)
                    robot.play_anim(
                        "anim_gotosleep_sleeping_01").wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(1)
                ##
                # Non, on a raté. Avancer, faire demi-tour, et réessayer.
                else:

                    print("State: failed to dock with charger, battery %s" %
                            str(round(robot.battery_voltage, 2)))
                    robot.play_anim_trigger(
                        cozmo.anim.Triggers.AskToBeRightedRight, ignore_body_track=True).wait_for_completed()
                    robot.set_head_angle(degrees(0)).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(0.1)

                    print("State: drive forward, turn around, and try again, battery %s" % str(
                        round(robot.battery_voltage, 2)))
                    robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees - 180), accel=degrees(
                        80), angle_tolerance=None, is_absolute=True, num_retries=2).wait_for_completed()
                    robot.drive_straight(distance_mm(
                        90), speed_mmps(90)).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(0.5)
                    robot.drive_straight(distance_mm(
                        90), speed_mmps(90)).wait_for_completed()
                    robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                        80), angle_tolerance=None, is_absolute=True, num_retries=2).wait_for_completed()
                    robot.set_head_angle(
                        degrees(0), in_parallel=True).wait_for_completed()
                    robot.wait_for_all_actions_completed()
                    time.sleep(0.5)
                    if (charger.is_visible == False):
                        # nous savons où se trouve le chargeur

                        print("State: can't see charger after turnaround, try again, battery %s" % str(
                            round(robot.battery_voltage, 2)))
                        robot.play_anim_trigger(
                            cozmo.anim.Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
                        robot.set_head_angle(
                            degrees(0)).wait_for_completed()
                        robot.wait_for_all_actions_completed()

                        print(str(charger))
                        time.sleep(0.5)
                        try:
                            action = robot.go_to_object(charger, distance_mm(
                                110), RobotAlignmentTypes.LiftPlate, num_retries=3)
                            action.wait_for_completed()
                        finally:
                            pass
                        try:
                            action = robot.go_to_object(charger, distance_mm(
                                80), RobotAlignmentTypes.LiftPlate, num_retries=3)
                            action.wait_for_completed()
                        finally:
                            pass
                        robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(
                            80), angle_tolerance=None, is_absolute=True).wait_for_completed()
                        robot.wait_for_all_actions_completed()
                        time.sleep(0.5)
                        if (charger.is_visible == False):
                            # nous savons où se trouve le chargeur mais nous avons été délocalisés.
                            charger = None
                            robot.world.charger = None
                            robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeReaction, ignore_body_track=True,
                                                    ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
                            robot.drive_straight(
                                distance_mm(-100), speed_mmps(50)).wait_for_completed()
                            robot.wait_for_all_actions_completed()

                            print("State: charger lost while docking, clearing map. battery %s" % str(
                                round(robot.battery_voltage, 2)))
                            time.sleep(1)
                            break
        else:
            # nous n'avons pas réussi à trouver le chargeur. Nous sommes revenus au freeplay.
            charger = None
            robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeReaction, ignore_body_track=True,
                                    ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
            robot.wait_for_all_actions_completed()

            print("State: fallback to 90 seconds of freeplay, battery %s" %
                    str(round(robot.battery_voltage, 2)))
            robot.start_freeplay_behaviors()
            # essayez le freeplay pendant 90 secondes, si vous trouvez un chargeur, arrêtez le freeplay.
            try:
                charger = robot.world.wait_for_observed_charger(
                    timeout=90, include_existing=True)

                print("State: found the charger within 90 seconds of playtime!, battery %s" % str(
                    round(robot.battery_voltage, 2)))
            except asyncio.TimeoutError:
                robot.stop_freeplay_behaviors()

                print("State: charger not found after 90 seconds, battery %s" % str(
                    round(robot.battery_voltage, 2)))
                robot.play_anim_trigger(
                    cozmo.anim.Triggers.CodeLabUnhappy, ignore_body_track=True).wait_for_completed()
                robot.set_head_angle(degrees(0)).wait_for_completed()
                robot.wait_for_all_actions_completed()
                time.sleep(1)
            finally:
                robot.stop_freeplay_behaviors()
                robot.wait_for_all_actions_completed()

                print("State: stop freeplay routine, battery %s" %
                        str(round(robot.battery_voltage, 2)))
                time.sleep(1)
            # après 90 secondes, fin du jeu libre
            robot.set_needs_levels(1, 1, 1)
            robot.world.disconnect_from_cubes()
    
    if robot.world.charger != None:
        charger = robot.world.charger

        print("State: updating charger location, battery %s" %
                str(round(robot.battery_voltage, 2)))

        print(str(charger))
        robot.world.charger = None
    
    if robot.is_picked_up == True:
        charger = None
        robot.world.charger = None

        print("State: robot picked up during freeplay, resetting charger, battery %s" % str(
            round(robot.battery_voltage, 2)))

    print("State: program loop complete, battery %s" %
            str(round(robot.battery_voltage, 2)))
    time.sleep(3)

# CONST
def run(sdk_conn_loop):
    '''The run method runs once the Cozmo SDK is connected.'''
    robot = sdk_conn_loop.wait_for_robot(timeout=1)

    try:
        connect_on_loop(cozmo_unleashed(robot), sdk_conn_loop)

    except KeyboardInterrupt as k:

        print("")

        print("Exit requested by user")
        SystemExit("Keyboard interrupt: %s" % k)

if __name__ == '__main__':
    cozmo.setup_basic_logging()
    # Cozmo peut rester sur le chargeur pour le moment
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    try:
        cozmo.connect_with_tkviewer(run, force_on_top=True)
    except cozmo.ConnectionError as e:
        SystemExit("A connection error with viewer occurred: %s" % e)

def __init__(self, thread_id, name, _q):
    threading.Thread.__init__(self)
    self.threadID = thread_id
    self.name = name
    self.q = _q
