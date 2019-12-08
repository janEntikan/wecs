from panda3d.core import Vec3
from panda3d.core import NodePath
from panda3d.core import CollisionSphere

from wecs import panda3d
from wecs import mechanics
from wecs.aspects import Aspect
from wecs.aspects import factory
from wecs.panda3d.animation import Animation

# An ontology of aspects:
# * Controllable beings on the map
#   `character`s are controllable entities with a "physical" presence (a Model)
#   `walking` is the ability to move around and interact with the map
#   To be `animated` means to be an Actor and Animated.
#   An `avatar` is a character that can walk and is animated.
#   A `spectator` is a character that floats and bumps into the map.
# * Things that control beings
#   `pc_mind` represents the input from the neural network between the player's ears.
#   `npc_mind` is a mind that executes a constant movement
# * Things that see the world
#   `first_person` is a first person camera
#   `third_person` is, unsurprisingly, a third person camera (with a few features).
# * Abstractions that are actually useful
#   The `player_character` is an `avatar` controlled by a `pc_mind` and seen through
#     the `third_person` camera.
#   A `non_player_character` is an `avatar` controlled by an `npc_mind`
#   A `game_map` is a model that you can bump / fall into.

character = Aspect([mechanics.Clock, panda3d.Position, panda3d.Scene,
                    panda3d.CharacterController, panda3d.Model])


def rebecca_bumper():
    return {
        'bumper': dict(
            shape=CollisionSphere,
            center=Vec3(0.0, 0.0, 1.0),
            radius=0.7,
        ),
    }
def rebecca_lifter():
    return {
        'lifter': dict(
            shape=CollisionSphere,
            center=Vec3(0.0, 0.0, 0.25),
            radius=0.5,
        ),
    }
walking = Aspect([panda3d.WalkingMovement, panda3d.CrouchingMovement, panda3d.SprintingMovement,
                  panda3d.InertialMovement, panda3d.BumpingMovement, panda3d.FallingMovement,
                  panda3d.JumpingMovement],
                 overrides = {
                     panda3d.BumpingMovement: dict(solids=factory(rebecca_bumper)),
                     panda3d.FallingMovement: dict(solids=factory(rebecca_lifter)),
                 },
)
animated = Aspect([panda3d.Actor, panda3d.AnimationPlayer, panda3d.VelocityAnimation],
    overrides={panda3d.VelocityAnimation: dict(
            animation_axes=[
                [], #x
                [
                    Animation("run_backward"),
                    Animation("walk_backward"),
                    Animation("idle"),
                    Animation("walk_forward"),
                    Animation("run_forward")
                ],  #y
                [], #z
            ],
            ranges=[[-20,20],[-20,20],[-20,20]]
        ),
    }
)

avatar = Aspect([character, walking, animated],
                overrides={panda3d.Model: dict(model_name='rebecca.bam')})


def spectator_bumper():
    return dict(
        solids={
            'bumper': dict(
                shape=CollisionSphere,
                center=Vec3(0.0, 0.0, 0.0),
                radius=0.1,
            ),
        },
    )
spectator = Aspect([character, panda3d.FloatingMovement, panda3d.BumpingMovement],
                   overrides={
                       panda3d.Model: dict(node=factory(lambda:NodePath('spectator'))),
                       panda3d.BumpingMovement: dict(solids=factory(spectator_bumper)),
                   },
)


pc_mind = Aspect([panda3d.Input])
npc_mind_constant = Aspect([panda3d.ConstantCharacterAI])
npc_mind_brownian = Aspect([panda3d.BrownianWalkerAI])


first_person = Aspect([panda3d.FirstPersonCamera])
third_person = Aspect([panda3d.TurntableCamera, panda3d.TurningBackToCameraMovement,
                       panda3d.CollisionZoom, panda3d.ThirdPersonCamera])


player_character = Aspect([avatar, pc_mind, third_person])
non_player_character = Aspect([avatar, npc_mind_constant])
