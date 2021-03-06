/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package org.meteoinfo.laboratory.gui;

import bibliothek.gui.dock.common.DefaultSingleCDockable;
import bibliothek.gui.dock.common.action.CAction;
import org.meteoinfo.console.JConsole;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.util.Locale;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.ImageIcon;
import javax.swing.JTextPane;
import javax.swing.SwingWorker;
import org.meteoinfo.chart.ChartPanel;
import org.python.core.Py;

/**
 *
 * @author yaqiang
 */
public class ConsoleDockable extends DefaultSingleCDockable {

    private String startupPath;
    private FrmMain parent;
    private PythonInteractiveInterpreter interp;

    public ConsoleDockable(FrmMain parent, String startupPath, String id, String title, CAction... actions) {
        super(id, title, actions);

        this.parent = parent;
        this.startupPath = startupPath;
        JConsole console = new JConsole();
        console.setLocale(Locale.getDefault());
        //System.out.println(console.getFont());
        console.setPreferredSize(new Dimension(600, 400));
        console.println(new ImageIcon(this.getClass().getResource("/org/meteoinfo/laboratory/resources/jython_small_c.png")));
        this.initializeConsole(console, parent.getCurrentFolder());

        this.getContentPane().add(console, BorderLayout.CENTER);
    }

    /**
     * Initialize console
     *
     * @param console
     */
    private void initializeConsole(JConsole console, String currentPath) {
        boolean isDebug = java.lang.management.ManagementFactory.getRuntimeMXBean().
                getInputArguments().toString().contains("jdwp");
        //String pluginPath = this.startupPath + File.separator + "plugins";
        //List<String> jarfns = GlobalUtil.getFiles(pluginPath, ".jar");

        //Issue java.lang.IllegalArgumentException: Cannot create PyString with non-byte value
        try {
            Py.getSystemState().setdefaultencoding("utf-8");
        } catch (Exception e){
            e.printStackTrace();
        }
        interp = new PythonInteractiveInterpreter(console);
        String path = this.startupPath + File.separator + "pylib";
        String toolboxPath = this.startupPath + "/toolbox";
        if (isDebug) {
            path = "D:/MyProgram/Java/MeteoInfoDev/MeteoInfoLab/pylib";
            toolboxPath = "D:/MyProgram/Java/MeteoInfoDev/toolbox";
        }        
        //console.println(path);
        //console.println(toolboxPath);

        //this.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
        try {
            interp.set("milapp", parent);
            interp.exec("import sys");
            interp.exec("import os");
            interp.exec("import datetime");
            //interp.exec("sys.setdefaultencoding('utf-8')");
            interp.exec("sys.path.append('" + path + "')");
            interp.exec("from milab import *");
            interp.exec("sys.path.append('" + toolboxPath + "')");
            interp.exec("import toolbox");
            interp.exec("from toolbox import *");            
            //interp.exec("import mipylib");
            //interp.exec("from mipylib.miscript import *");
            //interp.set("mipylib.miplot.milapp", parent);                        
            //interp.exec("from meteoinfo.numeric.JNumeric import *");
            //interp.exec("import mipylib.miscript as plt");
            //interp.exec("import meteoinfo.numeric.JNumeric as np");
            //interp.exec("import miscript");
            //for (String jarfn : jarfns) {
            //    interp.exec("sys.path.append('" + jarfn + "')");
            //}
        } catch (Exception e) {
            e.printStackTrace();
        }

        new Thread(interp).start();
        try {
            interp.exec("mipylib.miplot.isinteractive = True");
            interp.exec("mipylib.miplot.milapp1 = milapp");
            interp.exec("mipylib.minum.currentfolder = '" + currentPath + "'");
        } catch (Exception e) {
            e.printStackTrace();
        }
        //this.setCursor(Cursor.getDefaultCursor());
    }

    /**
     * Get interactive interpreter
     *
     * @return Interactive interpreter
     */
    public PythonInteractiveInterpreter getInterpreter() {
        return this.interp;
    }

    /**
     * Get console
     *
     * @return Console
     */
    public JConsole getConsole() {
        return this.interp.console;
    }

    /**
     * Set startup path
     *
     * @param path Startup path
     */
    public void setStartupPath(String path) {
        this.startupPath = path;
    }

    /**
     * Set parent frame
     *
     * @param parent Parent frame
     */
    public void setParent(FrmMain parent) {
        this.parent = parent;
    }

    /**
     * Run a command line
     *
     * @param command Command line
     */
    public void run(String command) {
        this.interp.console.println(command);
        //this.interp.exec(command);
        try {
            this.interp.exec(command);
        } catch (Exception e) {
        } finally {
            this.interp.out.print(">>> ");
            interp.exec("mipylib.miplot.isinteractive = True");
        }
    }

    /**
     * Run a command line
     *
     * @param command Command line
     */
    public void exec(String command) {
        this.interp.console.println("run script...");
        //this.interp.console.error(this.interp.err);
        this.interp.exec(command);
        //this.interp.push(command);
        this.interp.out.print(">>> ");
        interp.exec("mipylib.miplot.isinteractive = True");
    }

    /**
     * Run a Jython file text
     *
     * @param code Jython file text
     */
    public void runfile(String code) {
        try {
            this.interp.console.println("run script...");
            this.interp.setOut(this.interp.console.getOut());
            this.interp.setErr(this.interp.console.getErr());
            System.setOut(this.interp.console.getOut());
            System.setErr(this.interp.console.getErr());
            String encoding = EncodingUtil.findEncoding(code);
            if (encoding != null) {
                try {
                    interp.execfile(new ByteArrayInputStream(code.getBytes(encoding)));
                } catch (Exception e) {
                }
            } else {
                try {
                    interp.execfile(new ByteArrayInputStream(code.getBytes()));
                } catch (Exception e) {
                }
            }
            this.interp.out.print(">>> ");
        } catch (IOException ex) {
            Logger.getLogger(ConsoleDockable.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

//    /**
//     * Run Jython script
//     * @param code
//     */
//    public void runPythonScript(final String code) {
//
//        SwingWorker worker = new SwingWorker<String, String>() {
//            PrintStream oout = System.out;
//            PrintStream oerr = System.err;
//
//            @Override
//            protected String doInBackground() throws Exception {
//                JTextPane jTextPane_Output = interp.console.getTextPane();
//                JTextPaneWriter writer = new JTextPaneWriter(jTextPane_Output);
//                JTextPanePrintStream printStream = new JTextPanePrintStream(System.out, jTextPane_Output);
//                //jTextPane_Output.setText("");
//                interp.console.println("run script...");
//                interp.setOut(writer);
//                interp.setErr(writer);
//                System.setOut(printStream);
//                System.setErr(printStream);
//                
//                String encoding = EncodingUtil.findEncoding(code);
//                if (encoding != null) {
//                    try {
//                        interp.execfile(new ByteArrayInputStream(code.getBytes(encoding)));
//                    } catch (Exception e) {
//                    }
//                } else {
//                    try {
//                        interp.execfile(new ByteArrayInputStream(code.getBytes()));
//                    } catch (Exception e) {
//                    }
//                }
//                //interp.console.print(">>> ", Color.red);
//                return "";
//            }
//
//            @Override
//            protected void done() {
//                System.setOut(oout);
//                System.setErr(oerr);
//            }
//        };
//        worker.execute();
//    }
    /**
     * Run Jython script
     *
     * @param code
     */
    public void runPythonScript(final String code) {

        SwingWorker worker = new SwingWorker<String, String>() {
            PrintStream oout = System.out;
            PrintStream oerr = System.err;

            @Override
            protected String doInBackground() throws Exception {
                //JTextAreaWriter writer = new JTextAreaWriter(jTextArea_Output);
                //JTextAreaPrintStream printStream = new JTextAreaPrintStream(System.out, jTextArea_Output);
                //jTextArea_Output.setText("");

                JTextPane jTextPane_Output = interp.console.getTextPane();
                JTextPaneWriter writer = new JTextPaneWriter(jTextPane_Output);
                JTextPanePrintStream printStream = new JTextPanePrintStream(System.out, jTextPane_Output);
                
                interp.console.println("run script...");
                interp.setOut(writer);
                interp.setErr(writer);
                System.setOut(printStream);
                System.setErr(printStream);

                String encoding = "utf-8";
                try {
                    interp.exec("mipylib.miplot.isinteractive = False");
                    interp.exec("clf()");
                    interp.execfile(new ByteArrayInputStream(code.getBytes(encoding)));
                    interp.exec("mipylib.miplot.isinteractive = True");
                } catch (Exception e) {
                    e.printStackTrace();
                    interp.console.print(">>> ", Color.red);
                    interp.console.setStyle(Color.black);
                    //interp.console.setForeground(Color.black);
                    interp.exec("mipylib.miplot.isinteractive = True");
                }

                //String encoding = EncodingUtil.findEncoding(code);                
//                if (encoding != null) {
//                    try {
//                        interp.execfile(new ByteArrayInputStream(code.getBytes(encoding)));
//                    } catch (Exception e) {
//                        e.printStackTrace();
//                        interp.console.print(">>> ", Color.red);
//                        //interp.console.setStyle(Color.black);
//                        //interp.console.setForeground(Color.black);
//                    }
//                } else {
//                    try {
//                        interp.execfile(new ByteArrayInputStream(code.getBytes()));
//                    } catch (Exception e) {
//                        e.printStackTrace();
//                        interp.console.print(">>> ", Color.red);
//                        //interp.console.setStyle(Color.black);
//                        //interp.console.setForeground(Color.black);
//                    }
//                }
                return "";
            }

            @Override
            protected void done() {
                System.setOut(oout);
                System.setErr(oerr);
                ChartPanel cp = parent.getFigureDock().getCurrentFigure();
                if (cp != null){
                    cp.paintGraphics();
                }
            }
        };
        worker.execute();
    }
}
