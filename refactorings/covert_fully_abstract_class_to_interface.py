import os

from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.java.JavaLexer import JavaLexer
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


def get_java_files(directory):
    if not os.path.isdir(directory):
        raise ValueError("directory should be an absolute path of a directory!")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.split('.')[-1] == 'java':
                yield os.path.join(root, file), file


class CFACTIPropagationListener(JavaParserLabeledListener):

    def __init__(self, common_token_stream: CommonTokenStream = None):

        if common_token_stream is None:
            raise ValueError("common_token_stream is None")
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        print('not implemented!')


class FindAndConvertFullyAbstractClassListener(JavaParserLabeledListener):

    def __init__(self, common_token_stream: CommonTokenStream = None):

        if common_token_stream is None:
            raise ValueError("common_token_stream is None")
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

        self.class_declaration = None
        self.all_method_declarations = []
        self.all_field_declarations = []
        self.is_fully_abstract = False
        self.is_convertable = False

        self.messages = []

        self.TAB = "\t"
        self.NEW_LINE = "\n"
        self.code = ""

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        self.class_declaration = ctx
        type_declaration = ctx.parentCtx
        for modifier in type_declaration.classOrInterfaceModifier():
            if modifier.getText() == 'abstract':
                self.is_fully_abstract = True
                self.is_convertable = True
                return
        self.is_fully_abstract = False
        self.is_convertable = False

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if self.is_fully_abstract:
            if self.is_convertable:
                self.messages.append(
                    self.class_declaration.IDENTIFIER().getText() + ' is fully abstract and convertable.'
                )
                self.token_stream_rewriter.replaceRange(
                    from_idx=self.class_declaration.parentCtx.start.tokenIndex,
                    to_idx=self.class_declaration.start.tokenIndex,
                    text=f"interface"
                )
                for method_declaration in self.all_method_declarations:
                    class_body_declaration = method_declaration.parentCtx.parentCtx
                    for modifier in class_body_declaration.modifier():
                        if modifier.getText() == 'abstract' or modifier.getText() == 'public':
                            self.token_stream_rewriter.delete(
                                program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                                from_idx=modifier.start.tokenIndex,
                                to_idx=modifier.stop.tokenIndex + 1
                            )

                for field_declaration in self.all_field_declarations:
                    class_body_declaration = field_declaration.parentCtx.parentCtx
                    for modifier in class_body_declaration.modifier():
                        if modifier.getText() == 'public':
                            self.token_stream_rewriter.delete(
                                program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                                from_idx=modifier.start.tokenIndex,
                                to_idx=modifier.stop.tokenIndex + 1
                            )
            else:
                self.messages.append(
                    self.class_declaration.IDENTIFIER().getText() + ' is fully abstract but not convertable.'
                )
        else:
            self.messages.append(
                self.class_declaration.IDENTIFIER().getText() + ' is not fully abstract.'
            )

        self.class_declaration = None
        self.all_method_declarations = []
        self.all_field_declarations = []
        self.is_fully_abstract = False
        self.is_convertable = False

    def enterMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        self.all_method_declarations.append(ctx)
        class_body_declaration = ctx.parentCtx.parentCtx
        flag = False
        for modifier in class_body_declaration.modifier():
            if modifier.getText() == 'abstract':
                flag = True

            if modifier.getText() == 'private':
                self.is_convertable = False

        if not flag:
            self.is_fully_abstract = False

    def enterFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        self.all_field_declarations.append(ctx)
        for variable_declarator in ctx.variableDeclarators().variableDeclarator():
            if not variable_declarator.variableInitializer():
                self.is_fully_abstract = False
                return


class ReplaceParameterWithQueryAPI:

    def __init__(self, file_path):
        self.file_path = file_path
        self.new_file_path = file_path
        self.stream = FileStream(self.file_path, encoding="utf8")
        self.lexer = JavaLexer(self.stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = JavaParserLabeled(self.token_stream)
        self.tree = self.parser.compilationUnit()
        self.walker = ParseTreeWalker()

    def do_refactor(self):
        listener = FindAndConvertFullyAbstractClassListener(
            common_token_stream=self.token_stream
        )
        self.walker.walk(
            listener=listener,
            t=self.tree
        )

        print('\n'.join(listener.messages))

        with open(self.new_file_path, mode="w", newline="") as f:
            f.write(listener.token_stream_rewriter.getDefaultText())


if __name__ == '__main__':
    ReplaceParameterWithQueryAPI(
        file_path="C:\\Users\\asus\\Desktop\\desk\\University\\99002-CD (compiler)\\Project\\CodART"
                  "\\tests\\covert_fully_abstract_class_to_interface\\src\\Shape.java"
    ).do_refactor()
