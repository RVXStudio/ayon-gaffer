import GafferSceneUI
import IECore
import GafferArnold
import GafferScene
import Gaffer
import GafferOSL
import imath

class RVXShaderPlane(GafferScene.SceneNode):
    def __init__(self, name="RVXShaderPlane"):
        GafferScene.SceneNode.__init__(self, name)

        self["resolution"] = Gaffer.IntPlug(
            defaultValue=512, minValue=0
        )

        self["x_multiplier"] = Gaffer.FloatPlug(
            defaultValue=1, maxValue=10, minValue=0
        )
        self["y_multiplier"] = Gaffer.FloatPlug(
            defaultValue=1, minValue=0
        )

        self["shader"] = GafferScene.ShaderPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
        # self["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
        self["plane"] = GafferScene.Plane()


        self["oslcode"] = GafferOSL.OSLCode( "OSLCode" )
        self["oslcode"]["parameters"].addChild( Gaffer.FloatPlug( "xmult", defaultValue = 0.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
        self["oslcode"]["parameters"].addChild( Gaffer.FloatPlug( "ymult", defaultValue = 0.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
        self["oslcode"]["out"].addChild( Gaffer.V3fPlug( "uvout", direction = Gaffer.Plug.Direction.Out, defaultValue = imath.V3f( 0, 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, interpretation = IECore.GeometricData.Interpretation.Point ) )
        self["oslobject"] = GafferOSL.OSLObject( "OSLObject" )
        self["oslobject"]["primitiveVariables"].addChild( Gaffer.NameValuePlug( "uv", Gaffer.V3fPlug( "value", defaultValue = imath.V3f( 0, 0, 0 ), interpretation = IECore.GeometricData.Interpretation.UV ), True, "primitiveVariable", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
        self["oslcode"]["parameters"]["xmult"].setInput(self["x_multiplier"])
        self["oslcode"]["parameters"]["ymult"].setInput(self["y_multiplier"])
        self["oslcode"]["code"].setValue( 'vector i;\ngetattribute( "uv", i );\n\nfloat ratio = xmult/ymult;\n\nvector x = vector(i[0] * xmult, i[1] * ymult, i[2]); \n\nuvout = x;\n' )
        self["oslobject"]["interpolation"].setValue( 5 )
        self["oslobject"]["primitiveVariables"]["primitiveVariable"]["value"].setInput( self["oslcode"]["out"]["uvout"] )
        self["pathfilter"] = GafferScene.PathFilter( "PathFilter" )
        self["oslobject"]["filter"].setInput( self["pathfilter"]["out"] )
        self["pathfilter"]["paths"].setValue( IECore.StringVectorData( [ '*' ] ) )

        self["oslobject"]["in"].setInput(self["plane"]["out"])

        self["camera"] = GafferScene.Camera()
        self["camera"]["transform"]["translate"]["z"].setValue(1)
        self["ms"] = GafferScene.MergeScenes()
        self["light"] = GafferArnold.ArnoldLight( "SkydomeLight" )
        self["light"].loadShader( "skydome_light" )
        self["light"]["parameters"]["camera"].setValue(0.0)

        self["assignment"] = GafferScene.ShaderAssignment()
        self["assignment"]["in"].setInput( self["oslobject"]["out"] )
        self["assignment"]["shader"].setInput( self["shader"] )

        self["ms"]["in"]["in0"].setInput(self["assignment"]["out"])
        self["ms"]["in"]["in1"].setInput(self["camera"]["out"])
        self["ms"]["in"]["in2"].setInput(self["light"]["out"])



        self["opt"] = GafferScene.StandardOptions()
        self["opt"]["in"].setInput(self["ms"]["out"])
        self["opt"]["options"]["renderCamera"]["enabled"].setValue(True)
        self["opt"]["options"]["renderCamera"]["value"].setValue("/camera")
        self["opt"]["options"]["renderResolution"]["enabled"].setValue(True)
        #self["opt"]["options"]["renderResolution"][0].setValue(self["resolution"])
        self["opt"]["options"]["renderResolution"]["value"]["x"].setInput(self["resolution"])
        self["opt"]["options"]["renderResolution"]["value"]["y"].setInput(self["resolution"])


        # add the expression
        self["expr"] = Gaffer.Expression( "Expression" )

        self["expr"]["__in"].addChild( Gaffer.FloatPlug( "p0", defaultValue = 0.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
        self["expr"]["__in"].addChild( Gaffer.FloatPlug( "p1", defaultValue = 0.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
        self["expr"]["__out"].addChild( Gaffer.V2fPlug( "p0", direction = Gaffer.Plug.Direction.Out, defaultValue = imath.V2f( 1, 1 ), minValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
        self["plane"]["dimensions"].setInput( self["expr"]["__out"]["p0"] )
        self["expr"]["__in"]["p0"].setInput( self["oslcode"]["parameters"]["xmult"] )
        self["expr"]["__in"]["p1"].setInput( self["oslcode"]["parameters"]["ymult"] )
        self["expr"]["__engine"].setValue( 'python' )
        self["expr"]["__expression"].setValue( 'import imath\n\nx = parent["__in"]["p0"]\ny = parent["__in"]["p1"]\n\nratio = float(x/y)\nif ratio > 1:\n\tnew_y = float(1/ratio)\n\tnew_x = 1\nelse:\n   new_x = float(ratio)\n   new_y = 1\n\t\n\nparent["__out"]["p0"] = imath.V2f( new_x , new_y )' )


        self["out"].setInput( self["opt"]["out"] )
    


#GafferSceneUI.ShaderView.registerScene( "ai", "second", "/net-home/sveinbjorn/Desktop/plane.gfr" )
GafferSceneUI.ShaderView.registerScene( "ai", "RVXPlane", RVXShaderPlane )