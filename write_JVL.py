from aerosandbox import AVL
from typing import List
from pathlib import Path
import aerosandbox.numpy as np
from J import JetParam, JetControl, WingJSec

class JVL(AVL):
    def write_jvl(
            self,
            filepath,
            CLAF = True,
        ) -> None:
            """
            Writes a .avl file corresponding to this airplane to a filepath.

            For use with the AVL vortex-lattice-method aerodynamics analysis tool by Mark Drela at MIT.
            AVL is available here: https://web.mit.edu/drela/Public/web/avl/

            Args:
                filepath: filepath (including the filename and .avl extension) [string]
                    If None, this function returns the .avl file as a string.

            Returns: None

            """

            def clean(s):
                """
                Removes leading and trailing whitespace from each line of a multi-line string.
                """
                return "\n".join([line.strip() for line in s.split("\n")])

            airplane = self.airplane

            jvl_file = ""

            airplane_options = self.get_options(airplane)

            jvl_file += clean(
                f"""\
            {airplane.name}
            #Mach
            0        ! AeroSandbox note: This is overwritten later to match the current OperatingPoint Mach during the AVL run.
            #IYsym   IZsym   Zsym
            0       {1 if self.ground_effect else 0}   {self.ground_effect_height}
            #Sref    Cref    Bref
            {airplane.s_ref} {airplane.c_ref} {airplane.b_ref}
            #Xref    Yref    Zref
            {self.xyz_ref[0]} {self.xyz_ref[1]} {self.xyz_ref[2]}
            # CDp
            {airplane_options["profile_drag_coefficient"]}
            """
            )

            control_surface_counter = 0
            airfoil_counter = 0

            for wing in airplane.wings:

                wing_options = self.get_options(wing)

                spacing_line = f"{wing_options['chordwise_resolution']}   {self.AVL_spacing_parameters[wing_options['chordwise_spacing']]}"
                if wing_options["wing_level_spanwise_spacing"]:
                    spacing_line += f"   {wing_options['spanwise_resolution']}   {self.AVL_spacing_parameters[wing_options['spanwise_spacing']]}"

                jvl_file += clean(
                    f"""\
                #{"=" * 79}
                SURFACE
                {wing.name}
                #Nchordwise  Cspace  [Nspanwise   Sspace]
                {spacing_line}
                
                """
                )

                if wing_options["component"] is not None:
                    jvl_file += clean(
                        f"""\
                    COMPONENT
                    {wing_options['component']}
                        
                    """
                    )

                if wing.symmetric:
                    jvl_file += clean(
                        """\
                    YDUPLICATE
                    0
                        
                    """
                    )

                if wing_options["no_wake"]:
                    jvl_file += clean(
                        """\
                    NOWAKE
                    
                    """
                    )

                if wing_options["no_alpha_beta"]:
                    jvl_file += clean(
                        """\
                    NOALBE
                    
                    """
                    )

                if wing_options["no_load"]:
                    jvl_file += clean(
                        """\
                    NOLOAD
                    
                    """
                    )

                ### Build up a buffer of the control surface strings to write to each section
                control_surface_commands: List[List[str]] = [[] for _ in wing.xsecs]
                for i, xsec in enumerate(wing.xsecs[:-1]):
                    for surf in xsec.control_surfaces:
                        xhinge = (
                            surf.hinge_point if surf.trailing_edge else -surf.hinge_point
                        )
                        sign_dup = 1 if surf.symmetric else -1

                        command = clean(
                            f"""\
                            CONTROL
                            #name, gain, Xhinge, XYZhvec, SgnDup
                            {surf.name} 1 {xhinge:.8g} 0 0 0 {sign_dup}
                            """
                        ) + "\n"


                        control_surface_commands[i].append(command)
                        # control_surface_commands[i + 1].append(command)

                ### Write the commands for each wing section
                for i, xsec in enumerate(wing.xsecs):

                    xsec_options = self.get_options(xsec)

                    xsec_def_line = f"{xsec.xyz_le[0]:.8g} {xsec.xyz_le[1]:.8g} {xsec.xyz_le[2]:.8g} {xsec.chord:.8g} {xsec.twist:.8g}"
                    if not wing_options["wing_level_spanwise_spacing"]:
                        xsec_def_line += f"   {xsec_options['spanwise_resolution']}   {self.AVL_spacing_parameters[xsec_options['spanwise_spacing']]}"

                    if xsec_options["cl_alpha_factor"] is None:
                        claf_line = f"{1 + 0.77 * xsec.airfoil.max_thickness()}  # Computed using rule from avl_doc.txt"
                    else:
                        claf_line = f"{xsec_options['cl_alpha_factor']}"

                    af_filepath = Path(str(filepath) + f".af{airfoil_counter}")
                    airfoil_counter += 1
                    xsec.airfoil.repanel(50).write_dat(
                        filepath=af_filepath, include_name=True
                    )

                    jvl_file += clean(
                        f"""\
                    #{"-" * 50}
                    SECTION
                    #Xle    Yle    Zle     Chord   Ainc  [Nspanwise   Sspace]
                    {xsec_def_line}
                    
                    AFIL
                    {af_filepath}
                    
                    """
                    )
                    if CLAF:
                        jvl_file += clean(
                            f"""\
                        CLAF
                        {claf_line}
                        
                        """
                        )
                    for control_surface_command in control_surface_commands[i]:
                        jvl_file += control_surface_command
                    
                    # **JETCONTROL and JETPARAM Handling**
                    if isinstance(xsec, WingJSec):
                        for jet in xsec.jet_controls:
                            jvl_file += clean(
                                f"""\
                                JETCONTROL
                                {jet.jet_name} {jet.gain:.3f} {jet.sgn_dup:.3f}
                                """
                            ) + "\n"

                        for param in xsec.jet_params:
                            jvl_file += clean(
                                f"""\
                                JETPARAM
                                {param.hdisk:.3f} {param.fh:.3f} {param.djet0:.3f} {param.djet1:.3f} {param.djet3:.6f}
                                """
                            ) + "\n"

            filepath = Path(filepath)
            for i, fuse in enumerate(airplane.fuselages):
                fuse_filepath = Path(str(filepath) + f".fuse{i}")
                self.write_avl_bfile(fuselage=fuse, filepath=fuse_filepath)
                fuse_options = self.get_options(fuse)

                jvl_file += clean(
                    f"""\
                #{"=" * 50}
                BODY
                {fuse.name}
                {fuse_options['panel_resolution']} {self.AVL_spacing_parameters[fuse_options['panel_spacing']]}
                
                BFIL
                {fuse_filepath}
                
                TRANSLATE
                0 {np.mean([x.xyz_c[1] for x in fuse.xsecs]):.8g} 0
                
                """
                )

            if filepath is not None:
                with open(filepath, "w+") as f:
                    f.write(jvl_file)