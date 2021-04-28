def Wrapper(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.wrapper.Wrapper` instance"""
    from confetti.wrappers.wrapper import Wrapper

    return Wrapper(*args, **kwargs)


def DialsCosym(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_cosym.DialsCosym` instance"""
    from confetti.wrappers.dials_cosym import DialsCosym

    return DialsCosym(*args, **kwargs)


def DialsEstimateResolution(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_estimate_resolution.DialsEstimateResolution` instance"""
    from confetti.wrappers.dials_estimate_resolution import DialsEstimateResolution

    return DialsEstimateResolution(*args, **kwargs)


def Parrot(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.parrot.Parrot` instance"""
    from confetti.wrappers.parrot import Parrot

    return Parrot(*args, **kwargs)


def DialsMerge(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_merge.DialsMerge` instance"""
    from confetti.wrappers.dials_merge import DialsMerge

    return DialsMerge(*args, **kwargs)


def DialsImport(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_import.DialsImport` instance"""
    from confetti.wrappers.dials_import import DialsImport

    return DialsImport(*args, **kwargs)


def DialsRefine(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_refine.DialsRefine` instance"""
    from confetti.wrappers.dials_refine import DialsRefine

    return DialsRefine(*args, **kwargs)


def DialsExport(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_export.DialsExport` instance"""
    from confetti.wrappers.dials_export import DialsExport

    return DialsExport(*args, **kwargs)


def DialsIntegrate(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_integrate.DialsIntegrate` instance"""
    from confetti.wrappers.dials_integrate import DialsIntegrate

    return DialsIntegrate(*args, **kwargs)


def DialsFindSpots(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_find_spots.DialsFindSpots` instance"""
    from confetti.wrappers.dials_find_spots import DialsFindSpots

    return DialsFindSpots(*args, **kwargs)


def DialsIndex(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_index.DialsIndex` instance"""
    from confetti.wrappers.dials_index import DialsIndex

    return DialsIndex(*args, **kwargs)


def Refmac(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.refmac.Refmac` instance"""
    from confetti.wrappers.refmac import Refmac

    return Refmac(*args, **kwargs)


def Cad(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.cad.Cad` instance"""
    from confetti.wrappers.cad import Cad

    return Cad(*args, **kwargs)


def Buccaneer(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.buccaneer.Buccaneer` instance"""
    from confetti.wrappers.buccaneer import Buccaneer

    return Buccaneer(*args, **kwargs)


def Ctruncate(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.ctruncate.Ctruncate` instance"""
    from confetti.wrappers.ctruncate import Ctruncate

    return Ctruncate(*args, **kwargs)


def MtzDump(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.mtzdmp.MtzDump` instance"""
    from confetti.wrappers.mtzdmp import MtzDump

    return MtzDump(*args, **kwargs)


def Phaser(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.phaser.Phaser` instance"""
    from confetti.wrappers.phaser import Phaser

    return Phaser(*args, **kwargs)


def Reindex(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.reindex.Reindex` instance"""
    from confetti.wrappers.reindex import Reindex

    return Reindex(*args, **kwargs)


def Shelxe(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.shelxe.Shelxe` instance"""
    from confetti.wrappers.shelxe import Shelxe

    return Shelxe(*args, **kwargs)


def Mtz2Various(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.mtz2various.Mtz2Various` instance"""
    from confetti.wrappers.mtz2various import Mtz2Various

    return Mtz2Various(*args, **kwargs)


def DialsScale(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.dials_scale.DialsScale` instance"""
    from confetti.wrappers.dials_scale import DialsScale

    return DialsScale(*args, **kwargs)


def FreeRFlag(*args, **kwargs):
    """:py:obj:`~confetti.wrappers.freerflag.FreeRFlag` instance"""
    from confetti.wrappers.freerflag import FreeRFlag

    return FreeRFlag(*args, **kwargs)


def touch(fname, content='', mode='wb'):
    with open(fname, mode) as fhandle:
        fhandle.write(content)
    fhandle.close()
