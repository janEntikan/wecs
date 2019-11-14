from dataclasses import field

from wecs.core import Component
from wecs.core import System
from wecs.core import and_filter
from wecs.core import or_filter

from .input import Input
from .character import CharacterController
from .model import Model
from .model import Scene
from .model import Clock


def clamp_list(to_clamp, floor, ceiling):
    clamped = []
    for i in to_clamp:
        clamped.append(min(max(i, floor), ceiling))
    return clamped

# Animations:
# Idle
# Crouch/Walk/Run/Sprint/ forward/backward/left/right
# Flying/Jumping/Falling/Landing


@Component()
class Animation:
    to_play: list = field(default_factory=list)
    playing: list = field(default_factory=list)
    blends: list = field(default_factory=list)
    framerate: int = 1


class AnimateCharacter(System):
    entity_filters = {
        'animated_character': and_filter([
            Animation,
            Model,
            CharacterController
        ])
    }

    def update(self, entities_by_filter):
        for entity in entities_by_filter['animated_character']:
            controller = entity[CharacterController]
            animation = entity[Animation]
            actor = entity[Model].node

            # vertical animation
            vertical_speed = (controller.translation.z*10)
            blends = [1]
            if vertical_speed > 0.1:
                animation.to_play = ["jumping"]
            elif vertical_speed < -0.1:
                animation.to_play = ["falling"]
            else:
                # forward animation
                if controller.crouches:
                    # TODO: Don't crouch instantly but ease in (bounce?).
                    initial = "crouch"
                else:
                    initial = "idle"
                animation.to_play = [initial, "walk_forward", "run_forward"]
                forward_speed = abs(controller.translation.y*3)
                idle = max(0, (1 - forward_speed * 2))
                walk = 1 - abs(forward_speed - 0.5) * 2
                run = max(0, forward_speed * 2 - 1)
                blends = [idle, walk, run]
                # strafe animation
                strafe_speed = (controller.translation.x*10)
                if not strafe_speed == 0:
                    blends.append(abs(strafe_speed))
                    if strafe_speed > 0:
                        animation.to_play.append("walk_right")
                    elif strafe_speed < 0:
                        animation.to_play.append("walk_left")

                animation.framerate = (0.5+(forward_speed + abs(strafe_speed)))
                # If walking backwards simply play the animation in reverse
                # Only do this when there's no animations for walking backwards?
                if controller.translation.y < 0:
                    animation.framerate = -animation.framerate

            animation.blends = blends

            if Input in entity:
                print(animation.blends)
                print(animation.playing)


class Animate(System):
    entity_filters = {
        'animation': and_filter([
            Animation,
            Model,
        ])
    }
    def init_entity(self, filter_name, entity):
        print(entity[Model].node.getAnimNames())

    def update(self, entities_by_filter):
        for entity in entities_by_filter['animation']:
            animation = entity[Animation]
            actor = entity[Model].node
            if not animation.playing == animation.to_play:
                if len(animation.to_play) > 0:
                    actor.enableBlend()
                else:
                    actor.disableBlend()

                #Stop animations not in to_play.
                for name in animation.playing:
                    if not name in animation.to_play:
                        actor.stop(name)
                        actor.setControlEffect(name, 0)

                #Play newly added animations.
                for n, name in enumerate(animation.to_play):
                    if name not in animation.playing:
                        actor.loop(name)
                animation.playing = animation.to_play

            # Set blends each frame
            for b, blend in enumerate(animation.blends):
                if b < len(animation.playing):
                    name = animation.playing[b]
                    actor.setControlEffect(name, blend/len(animation.playing))

            # Set framerate each frame
            for name in animation.playing:
                actor.setPlayRate(animation.framerate, name)
