from dataclasses import field
from math import sin

from wecs.core import Component
from wecs.core import System
from wecs.core import and_filter
from wecs.core import or_filter

from .input import Input
from .character import CharacterController, FallingMovement
from .model import Model
from .model import Scene
from .model import Clock


class Animation:
    def __init__(self, name="idle", blend=1, fade_in=1, fade_out=1, framerate=1):
        self.name = name
        self.blend = blend
        self.current_blend = 0
        self.fade_in_speed = fade_in
        self.fade_out_speed = fade_out
        self.framerate = framerate
        self.play_once = False

    def activate(self, actor):
        if self.play_once:
            actor.play(self.name)
        else:
            actor.loop(self.name)

    def update(self, actor, animation_player):
        if not self in animation_player.to_play:
            self.die(actor, animation_player)
        else:
            self.fading_in()
        actor.setControlEffect(self.name, self.current_blend)
        actor.setPlayRate(self.framerate, self.name)

    def die(self, actor, animation_player):
        if not self.fading_out(actor):
            actor.stop(self.name)
            animation_player.playing.remove(self)

    def fading_out(self):
        self.blend -= self.fade_out
        if self.blend <= 0:
            return False
        return True

    def fading_in(self):
        if self.current_blend < self.blend:
            self.current_blend += self.fade_in
        if self.current_blend >= self.blend:
            self.current_blend = self.blend


@Component()
class VelocityAnimation:
    animation_axes: list = field(default_factory=[[],[],[]]) #Three lists for: x, y, z
    ranges: list = field(default_factory=[[],[],[]]) #Three lists for: x, y, z


@Component()
class AnimationPlayer:
    to_play: list = field(default_factory=list)
    playing: list = field(default_factory=list)


class AnimateByVelocity(System):
    entity_filters = {
        'animation': and_filter([
            AnimationPlayer,
            VelocityAnimation,
            CharacterController,
            Model,
        ])
    }

    def update(self, entities_by_filter):
        for entity in entities_by_filter['animation']:
            animation_player = entity[AnimationPlayer]

            velocity_animations = entity[VelocityAnimation]
            speed_range = velocity_animations
            velocity = entity[CharacterController].last_translation_speed
            for axis, animations in enumerate(velocity_animations.animation_axes):
                for a, animation in enumerate(animations):
                    if animation not in animation_player.to_play:
                        animation_player.to_play.append(animation)
                    blend = 0
                    speed = velocity[axis]
                    step_size = 1/len(animations)
                    step = a*step_size
                    if speed > step-(step_size/2) and speed < step+(step_size/2):
                        s = sin(speed)
                        if a%2: #invert curve if animation is odd
                            s = -s
                        blend = s
                    animation.blend = animation.current_blend = blend


class Animate(System):
    entity_filters = {
        'animation': and_filter([
            AnimationPlayer,
            Model,
        ])
    }

    def update(self, entities_by_filter):
        for entity in entities_by_filter['animation']:
            animation_player = entity[AnimationPlayer]
            actor = entity[Model].node
            actor.disableBlend()
            if len(animation_player.playing) > 0:
                actor.enableBlend()
            #Activate any new animations.
            for a, animation in enumerate(animation_player.to_play):
                if animation not in animation_player.playing:
                    animation.activate(actor)
                    animation_player.playing.append(animation)
            #Update currently playing animations
            for animation in animation_player.playing:
                animation.update(actor, animation_player)
